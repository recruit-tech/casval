import json
import os
import uuid
from enum import Enum
from enum import auto

import kubernetes.client as k8s
import requests
from kubernetes.client.rest import ApiException


class DeploymentStatus(Enum):
    NOT_EXIST = auto()
    NOT_READY = auto()
    RUNNING = auto()


class Deployer:

    UID_PREFIX = "casval-"

    def __init__(self, uid):
        self.host = None
        self.port = None
        self.uid = uid if uid != None else Deployer.UID_PREFIX + uuid.uuid4().hex
        self.status = DeploymentStatus.NOT_EXIST

    def create(self):
        raise NotImplementedError()

    def delete(self):
        raise NotImplementedError()

    def is_ready(self):
        raise NotImplementedError()


class LocalDeployer(Deployer):
    def __init__(self, uid):
        super().__init__(uid)
        self.host = os.getenv("OPENVAS_OMP_ENDPOINT", "127.0.0.1")
        self.port = os.getenv("OPENVAS_OMP_PORT", 9390)

    def create(self):
        return {"status": DeploymentStatus.RUNNING, "host": self.host, "port": self.port, "uid": self.uid}

    def delete(self):
        return

    def is_ready(self):
        return True


class KubernetesDeployer(Deployer):

    OPENVAS_CONTAINER_IMAGE = "mikesplain/openvas:9"
    CONTAINER_USE_CPU_LIMIT = "400m"
    CONTAINER_USE_MEMORY_LIMIT = "4Gi"
    DEFAULT_SERVICE_PORT = 443
    GCP_METADATA_API_TOKEN_ENDPOINT = (
        "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token"
    )

    def __init__(self, uid):
        super().__init__(uid)
        self.namespace = os.getenv("KUBERNETES_NAMESPACE", "default")
        self.client = self._client()
        self.status, self.host, self.port = self._get_status()

    def create(self):
        if self.status == DeploymentStatus.NOT_EXIST:
            self._create_deployment()

            try:
                self._create_service()
            except Exception:
                self._delete_deployment()
                raise

            self.status, self.host, self.port = self._get_status()

        return {"status": self.status, "host": self.host, "port": self.port, "uid": self.uid}

    def delete(self):
        if self.status != DeploymentStatus.NOT_EXIST:
            self._delete_deployment()
            self._delete_service()

    def is_ready(self):
        return bool(self.host and self.port and self.status == DeploymentStatus.RUNNING)

    def _get_status(self):
        status = DeploymentStatus.NOT_READY
        host = None
        port = None

        try:
            deployment = self._read_deployment()
            available_replicas = deployment.status.available_replicas

            service = self._read_service()
            if service.status.load_balancer.ingress is not None:
                host = service.status.load_balancer.ingress[0].ip
                port = service.spec.ports[0].port

            if available_replicas and host and port:
                status = DeploymentStatus.RUNNING

        except ApiException as e:
            if e.status == 404:
                status = DeploymentStatus.NOT_EXIST
            else:
                raise

        return status, host, port

    def _client(self):
        config = k8s.Configuration()
        config.api_key["authorization"] = "Bearer " + self._get_credential()
        config.host = os.getenv("KUBERNETES_MASTER_SERVER", "localhost")
        config.verify_ssl = False
        return k8s.ApiClient(config)

    def _get_credential(self):
        headers = {"Metadata-Flavor": "Google"}
        res = requests.get(KubernetesDeployer.GCP_METADATA_API_TOKEN_ENDPOINT, headers=headers)
        return json.loads(res.text)["access_token"]

    def _create_service(self):
        service_port = k8s.V1ServicePort(
            name=self.uid[-14:],
            port=KubernetesDeployer.DEFAULT_SERVICE_PORT,
            target_port=os.getenv("OPENVAS_OMP_PORT", 9390),
        )
        service_spec = k8s.V1ServiceSpec(
            type="LoadBalancer", ports=[service_port], selector={"app.kubernetes.io/name": self.uid}
        )
        service_metadata = k8s.V1ObjectMeta(name=self.uid, labels={"app.kubernetes.io/name": self.uid})
        service = k8s.V1Service(spec=service_spec, metadata=service_metadata)
        return k8s.CoreV1Api(self.client).create_namespaced_service(self.namespace, service)

    def _create_deployment(self):
        REPLICAS = 1

        container_port = k8s.V1ContainerPort(
            name=self.uid[-14:], container_port=os.getenv("OPENVAS_OMP_PORT", 9390)
        )
        resources = k8s.V1ResourceRequirements(
            limits={
                "cpu": KubernetesDeployer.CONTAINER_USE_CPU_LIMIT,
                "memory": KubernetesDeployer.CONTAINER_USE_MEMORY_LIMIT,
            }
        )
        container = k8s.V1Container(
            image=KubernetesDeployer.OPENVAS_CONTAINER_IMAGE,
            name=self.uid,
            image_pull_policy="IfNotPresent",
            ports=[container_port],
            resources=resources,
        )
        toleration = k8s.V1Toleration(effect="NoSchedule", key="Scanners", operator="Exists")
        pod_spec = k8s.V1PodSpec(containers=[container], tolerations=[toleration])
        pod_metadata = k8s.V1ObjectMeta(name=self.uid, labels={"app.kubernetes.io/name": self.uid})
        pod_template = k8s.V1PodTemplateSpec(spec=pod_spec, metadata=pod_metadata)
        selector = k8s.V1LabelSelector(match_labels={"app.kubernetes.io/name": self.uid})
        deployment_spec = k8s.V1DeploymentSpec(replicas=REPLICAS, selector=selector, template=pod_template)
        deployment_metadata = k8s.V1ObjectMeta(name=self.uid, labels={"app.kubernetes.io/name": self.uid})
        deployment = k8s.V1Deployment(spec=deployment_spec, metadata=deployment_metadata)
        return k8s.AppsV1Api(self.client).create_namespaced_deployment(self.namespace, deployment)

    def _delete_service(self):
        return k8s.CoreV1Api(self.client).delete_namespaced_service(self.uid, self.namespace)

    def _delete_deployment(self):
        return k8s.AppsV1Api(self.client).delete_namespaced_deployment(self.uid, self.namespace)

    def _read_service(self):
        return k8s.CoreV1Api(self.client).read_namespaced_service(self.uid, self.namespace)

    def _read_deployment(self):
        return k8s.AppsV1Api(self.client).read_namespaced_deployment(self.uid, self.namespace)

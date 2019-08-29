import json
import os
import uuid
from abc import ABCMeta
from abc import abstractmethod
from enum import Enum
from enum import auto

import kubernetes.client as k8s
import requests
from flask import current_app as app
from kubernetes.client.rest import ApiException


class Deployer(metaclass=ABCMeta):
    """
    Abstruct Deployer's class

    Required create public method
    """

    @abstractmethod
    def create(self, name: str):
        raise NotImplementedError()

    @abstractmethod
    def delete(self, name: str):
        raise NotImplementedError()

    @abstractmethod
    def ip(self):
        raise NotImplementedError()

    @abstractmethod
    def port(self):
        raise NotImplementedError()


class LocalDeployer(Deployer):
    def __ini__(self, options={}) -> None:
        return

    def create(self, uuid=None, container_image=None, container_port=None):
        return {
            "status": DeployerStatus.RUNNING,
            "ip": "127.0.0.1",
            "port": container_port,
            "uuid": "Nothing",
        }

    def delete(self, uuid):
        return

    @property
    def ip(self):
        return self.__ip

    @ip.setter
    def ip(self, ip):
        self.__ip = ip

    @property
    def port(self):
        return self.__port

    @port.setter
    def port(self, port):
        self.__port = port


class KubernetesDeployer(Deployer):
    def __init__(self, options={}) -> None:
        self.uuid = None
        self.client = None
        self.ip = None
        self.port = 443
        self.container_port = None
        self.container_image = None
        self.info = None
        self.host = os.getenv("KUBERNETES_SERVER", "localhost")
        self.namespace = os.getenv("KUBERNETES_NAMESPACE", "default")

        if options.get("kubernetes_server") is not None:
            self.host = options["kubernetes_server"]

        if options.get("namespace") is not None:
            self.namespace = options["namespace"]

        self.client = self._client()

    def create(self, uuid=None, container_image=None, container_port=None):
        if uuid == None:
            self.uuid = self._uuid()
        else:
            self.uuid = uuid

        self.container_image = container_image
        self.container_port = container_port

        try:
            self.info = self.get_info()
            if self.info["status"] != DeployerStatus.NOT_EXIST:
                return self.info

            self._create_deployment()
            self._create_service()

            return self.get_info()

        except CreateServiceException as e:
            self._delete_deployment()
            app.logger.exception(e)

        except Exception as e:
            app.logger.exception(e)

        return self._get_info(DeployerStatus.FAILED)

    def delete(self, uuid: str) -> None:
        self.uuid = uuid

        try:
            self.info = self.get_info()
            if self.info["status"] == DeployerStatus.NOT_EXIST:
                raise ResourceNotFoundException

            self._delete_deployment()
            self._delete_service()

        except Exception as e:
            app.logger.exception(e)

        return

    def get_info(self, uuid="") -> dict:
        if uuid != "":
            self.uuid = uuid

        try:
            deployment = self._read_deployment()
            available_replicas = deployment.status.available_replicas

            service = self._read_service()
            self.port = service.spec.ports[0].port

            if service.status.load_balancer.ingress is not None:
                self.ip = service.status.load_balancer.ingress[0].ip

            if available_replicas and self.ip and self.port:
                return self._get_info(DeployerStatus.RUNNING)

            return self._get_info(DeployerStatus.WAITING)

        except ApiException as e:
            if e.status == 404:
                return self._get_info(DeployerStatus.NOT_EXIST)

            app.logger.exception(e)

        except Exception as e:
            app.logger.exception(e)

        return self._get_info(DeployerStatus.FAILED)

    def _uuid(self):
        return "pre" + str(uuid.uuid4())

    def _client(self):
        configuration = k8s.Configuration()
        configuration.api_key["authorization"] = "Bearer " + self._get_credential()
        configuration.host = self.host
        configuration.verify_ssl = False
        return k8s.ApiClient(configuration)

    def _get_credential(self):
        GOOGLE_METADATA_API = (
            "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token"
        )

        credential = os.getenv("KUBERNETES_CREDENTIAL")
        if credential is None:
            try:
                headers = {"Metadata-Flavor": "Google"}
                res = requests.get(GOOGLE_METADATA_API, headers=headers)
                credential = json.loads(res.text).get("access_token", "")
            except requests.exceptions.ConnectionError:
                credential = ""
            except Exception as e:
                credential = ""
                app.logger.exception(e)

        return credential

    def _create_service(self):
        api_instance = k8s.CoreV1Api(self.client)
        service_port = k8s.V1ServicePort(
            name=self.uuid.split("-")[0], port=self.port, target_port=self.container_port, protocol="TCP"
        )
        service_spec = k8s.V1ServiceSpec(
            type="LoadBalancer", ports=[service_port], selector={"app.kubernetes.io/name": self.uuid}
        )
        service_metadata = k8s.V1ObjectMeta(name=self.uuid, labels={"app.kubernetes.io/name": self.uuid})
        service = k8s.V1Service(spec=service_spec, metadata=service_metadata)

        try:
            return api_instance.create_namespaced_service(self.namespace, service)
        except Exception as e:
            raise CreateServiceException(e)

    def _create_deployment(self):
        """
        Deployments must toleration "Scanners" key.
        """

        REPLICAS = 1
        api_instance = k8s.AppsV1Api(self.client)
        container_port = k8s.V1ContainerPort(
            name=self.uuid.split("-")[0], container_port=self.container_port, protocol="TCP"
        )
        resources = k8s.V1ResourceRequirements(limits={"cpu": "400m", "memory": "800Mi"})
        container = k8s.V1Container(
            image=self.container_image,
            name=self.uuid,
            image_pull_policy="IfNotPresent",
            ports=[container_port],
            resources=resources,
        )
        toleration = k8s.V1Toleration(effect="NoSchedule", key="Scanners", operator="Exists")

        pod_spec = k8s.V1PodSpec(containers=[container], tolerations=[toleration])
        pod_metadata = k8s.V1ObjectMeta(name=self.uuid, labels={"app.kubernetes.io/name": self.uuid})

        pod_template = k8s.V1PodTemplateSpec(spec=pod_spec, metadata=pod_metadata)
        deployment_spec_selector = k8s.V1LabelSelector(match_labels={"app.kubernetes.io/name": self.uuid})
        deployment_spec = k8s.V1DeploymentSpec(
            replicas=REPLICAS, selector=deployment_spec_selector, template=pod_template
        )
        deployment_metadata = k8s.V1ObjectMeta(name=self.uuid, labels={"app.kubernetes.io/name": self.uuid})
        deployment = k8s.V1Deployment(spec=deployment_spec, metadata=deployment_metadata)

        try:
            return api_instance.create_namespaced_deployment(self.namespace, deployment)
        except Exception as e:
            raise CreateDeploymentException(e)

    def _delete_service(self):
        api_instance = k8s.CoreV1Api(self.client)
        try:
            return api_instance.delete_namespaced_service(self.uuid, self.namespace)
        except Exception as e:
            raise DeleteServiceException(e)

    def _delete_deployment(self):
        api_instance = k8s.AppsV1Api(self.client)
        try:
            return api_instance.delete_namespaced_deployment(self.uuid, self.namespace)
        except Exception as e:
            raise DeleteDeploymentException(e)

    def _read_service(self):
        api_instance = k8s.CoreV1Api(self.client)
        return api_instance.read_namespaced_service(self.uuid, self.namespace)

    def _read_deployment(self):
        api_instance = k8s.AppsV1Api(self.client)
        return api_instance.read_namespaced_deployment(self.uuid, self.namespace)

    def _get_info(self, status):
        return {"status": status, "ip": self.ip, "port": self.port, "uuid": self.uuid}

    @property
    def ip(self):
        return self.__ip

    @ip.setter
    def ip(self, ip):
        self.__ip = ip

    @property
    def port(self):
        return self.__port

    @port.setter
    def port(self, port):
        self.__port = port

    @property
    def container_port(self):
        return self.__container_port

    @container_port.setter
    def container_port(self, container_port):
        self.__container_port = container_port

    @property
    def container_image(self):
        return self.__container_image

    @container_image.setter
    def container_image(self, container_image):
        self.__container_image = container_image

    @property
    def host(self):
        return self.__host

    @host.setter
    def host(self, host):
        self.__host = host

    @property
    def info(self):
        return self.__info

    @info.setter
    def info(self, info):
        self.__info = info

    @property
    def namespace(self):
        return self.__namespace

    @namespace.setter
    def namespace(self, namespace):
        self.__namespace = namespace


class DeployerStatus(Enum):
    RUNNING = auto()
    WAITING = auto()
    FAILED = auto()
    NOT_EXIST = auto()


class DeployerException(Exception):
    pass


class KubernetesException(DeployerException):
    pass


class ResourceNotFoundException(DeployerException):
    pass


class CreateServiceException(KubernetesException):
    pass


class CreateDeploymentException(KubernetesException):
    pass


class DeleteServiceException(KubernetesException):
    pass


class DeleteDeploymentException(KubernetesException):
    pass

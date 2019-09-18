######################
## Master Node Pool
######################


resource "google_container_node_pool" "casval_cluster_master_node_pool" {
  provider = "google-beta"
  cluster            = "${google_container_cluster.casval_cluster.name}"
  initial_node_count = "1"
  location = "${data.google_compute_zones.available.names[0]}"

  management {
    auto_repair  = true
    auto_upgrade = false
  }

  name = "master-node-pool"

  autoscaling {
    min_node_count = 1
    max_node_count = 2
  }

  node_config {
    disk_size_gb    = "50"
    disk_type       = "pd-standard"
    image_type      = "COS"
    labels          {}
    local_ssd_count = "0"
    machine_type    = "${var.master_machine_type}"
    metadata        {}
    oauth_scopes    = ["https://www.googleapis.com/auth/cloud-platform"]
    preemptible     = false
    service_account = "default"
    taint {
      key = "CriticalAddonsOnly"
      value = "true"
      effect = "NO_SCHEDULE"
    }
  }

  project = "${var.project}"
}

######################
## Worker Node Pool
######################

resource "google_container_node_pool" "casval_cluster_worker_node_pool" {
  provider = "google-beta"
  cluster            = "${google_container_cluster.casval_cluster.name}"
  initial_node_count = "0"
  location = "${data.google_compute_zones.available.names[0]}"

  management {
    auto_repair  = true
    auto_upgrade = false
  }

  name = "worker-node-pool"

  autoscaling {
    min_node_count = 0
    max_node_count = 5
  }

  node_config {
    disk_size_gb    = "50"
    disk_type       = "pd-standard"
    image_type      = "COS"
    labels          {}
    local_ssd_count = "0"
    machine_type    = "${var.worker_machine_type}"
    metadata        {}
    oauth_scopes    = ["https://www.googleapis.com/auth/cloud-platform"]
    preemptible     = false
    service_account = "default"
    taint {
      key = "Scanners"
      value = "true"
      effect = "NO_SCHEDULE"
    }
  }


  project = "${var.project}"
}

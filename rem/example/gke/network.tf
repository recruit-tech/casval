######################
### VPC Network
######################

resource "google_compute_network" "casval_cluster_nat_network" {
  auto_create_subnetworks         = false
  delete_default_routes_on_create = false
  description                     = "k8s Cloud NAT用ネットワーク"
  name                            = "casval-cluster-nat-network"
  routing_mode                    = "REGIONAL"
  project = "${var.project}"
}

######################
### Sub Network
######################

resource "google_compute_subnetwork" "casval_cluster_nat_subnetwork" {
  name          = "casval-cluster-nat-subnetwork"
  network       = "${google_compute_network.casval_cluster_nat_network.self_link}"
  ip_cidr_range = "10.0.0.0/16"
  region        = "${var.region}"
  project	= "${var.project}"

  private_ip_google_access = true
}

######################
### Cloud Router
######################

resource "google_compute_router" "casval_cluster_router" {
  name    = "casval-cluster-router-1"
  region  = "${google_compute_subnetwork.casval_cluster_nat_subnetwork.region}"
  network = "${google_compute_network.casval_cluster_nat_network.self_link}"
  bgp {
    asn = 64514
  }
  project = "${var.project}"
}

######################
### Cloud Nat
######################

resource "google_compute_router_nat" "casval_cluster_nat" {
  name                               = "casval-cluster-nat"
  router                             = "${google_compute_router.casval_cluster_router.name}"
  region                             = "${var.region}"
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"

  source_subnetwork_ip_ranges_to_nat = "LIST_OF_SUBNETWORKS"
  subnetwork {
    name                    = "${google_compute_subnetwork.casval_cluster_nat_subnetwork.self_link}"
    source_ip_ranges_to_nat = ["ALL_IP_RANGES"]
  }
  project = "${var.project}"
}

######################
### Cloud Address
######################

resource "google_compute_address" "casval_cluster_nat_address" {
  count  = 1
  name   = "casval-cluster-nat-external-address-${count.index}"
  region = "${var.region}"
}
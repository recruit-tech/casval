######################
### Firewall
######################

resource "google_compute_firewall" "casval_allow_outboud_traffic" {
  allow {
    protocol = "all"
  }

  destination_ranges = ["0.0.0.0/0"]
  direction          = "EGRESS"
  disabled           = false
  name               = "casval-allow-outboud-traffic"
  network            = "${google_compute_network.casval_cluster_nat_network.name}"
  priority           = "1000"
  project = "${var.project}"
}

resource "google_compute_firewall" "casval_cluster_master" {
  allow {
    ports    = ["10250", "443"]
    protocol = "tcp"
  }

  direction     = "INGRESS"
  disabled      = false
  name          = "casval-cluster-master"
  network       = "${google_compute_network.casval_cluster_nat_network.name}"
  priority      = "800"
  source_ranges = ["172.16.0.0/28"]
  project = "${var.project}"
}

resource "google_compute_firewall" "casval_cluster_firewall_vms" {
  allow {
    ports    = ["1-65535"]
    protocol = "tcp"
  }

  allow {
    protocol = "icmp"
  }

  allow {
    ports    = ["1-65535"]
    protocol = "udp"
  }

  direction     = "INGRESS"
  disabled      = false
  name          = "casval-cluster-firewall-vms"
  network       = "${google_compute_network.casval_cluster_nat_network.name}"
  priority      = "1000"
  source_ranges = ["10.0.1.0/24"]
  project = "${var.project}"
}

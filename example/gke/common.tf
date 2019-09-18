provider "google" {
  project = "${var.project}"
  region  = "${var.region}"
}

provider "google-beta" {
  project = "${var.project}"
  region  = "${var.region}"
  version = "~> 2.5.0"
}

data "google_compute_zones" "available" {
  region = "${var.region}"
  status = "UP"
}

output "DB_NAME" {
  value = "${google_sql_database.casval.name}"
}

output "DB_USER" {
  value = "${google_sql_user.user.name}"
}

output "DB_PASSWORD" {
  value = "${google_sql_user.user.password}"
}

output "DB_INSTANCE_NAME" {
  value = "${google_sql_database_instance.master.connection_name}"
}

output "GCP_PROJECT_NAME" {
  value = "${var.project}"
}

output "GCP_REPORT_STORAGE_NAME" {
  value = "${google_storage_bucket.report_storage.id}"
}

output "OPENVAS_SCAN_ENDPOINT" {
  value = "${google_compute_address.casval_cluster_nat_address.address}"
}

output "KUBERNETES_MASTER_SERVER" {
  value = "https://${google_container_cluster.casval_cluster.endpoint}"
}

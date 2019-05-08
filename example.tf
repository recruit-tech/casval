variable "db_name" {
  default = "casval"
}

variable "db_user" {
  default = "root"
}

variable "db_password" {
  default = "admin123"
}

variable "db_tier" {
  default = "db-n1-standard-1"
}

variable "region" {
  default = "asia-east2"
}

variable "project" {
  default = "{YOUR_PROJECT_NAME}"
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

output "PASSWORD_SALT" {
  value = "${random_string.password_salt.result}"
}

resource "random_string" "password_salt" {
  length      = 32
  min_upper   = 4
  min_lower   = 4
  min_numeric = 4
  special     = false
}

resource "random_pet" "bucker_suffix" {}

provider "google" {
  project = "${var.project}"
  region  = "${var.region}"
}

resource "google_storage_bucket" "report_storage" {
  name     = "casval-report-${random_pet.bucker_suffix.id}"
  location = "${var.region}"
}

resource "google_sql_database_instance" "master" {
  database_version = "MYSQL_5_7"

  settings {
    tier = "${var.db_tier}"

    database_flags {
      name  = "character_set_server"
      value = "utf8mb4"
    }

    database_flags {
      name  = "default_time_zone"
      value = "+00:00"
    }
  }
}

resource "google_sql_user" "user" {
  name     = "${var.db_user}"
  instance = "${google_sql_database_instance.master.name}"
  password = "${var.db_password}"
}

resource "google_sql_database" "casval" {
  name      = "${var.db_name}"
  instance  = "${google_sql_database_instance.master.name}"
  charset   = "utf8mb4"
  collation = "utf8mb4_unicode_ci"
}

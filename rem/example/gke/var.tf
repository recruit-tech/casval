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

variable "worker_machine_type" {
  default = "n1-standard-4"
}

variable "master_machine_type" {
  default = "g1-small"
}

variable "project" {
  default = "{YOUR_PROJECT_NAME}"
}

variable "authorized_networks" {
  default = "{YOUR_CIDR_BLOCK}"
}
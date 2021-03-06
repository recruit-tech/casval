######################
### CloudSQL
######################

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

    backup_configuration {
      enabled = true
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

resource "random_pet" "bucker_suffix" {}

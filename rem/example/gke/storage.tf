######################
### Storage
######################

resource "google_storage_bucket" "report_storage" {
  name     = "casval-report-${random_pet.bucker_suffix.id}"
  location = "${var.region}"
}

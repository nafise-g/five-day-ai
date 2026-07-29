variable "gcp_project_id" {
  description = "GCP Project ID for EcoStream deployment"
  type        = string
  default     = "ecostream-project-prod"
}

variable "gcp_region" {
  description = "GCP deployment region"
  type        = string
  default     = "us-central1"
}

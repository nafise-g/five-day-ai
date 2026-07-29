# Infrastructure as Code (IaC) configuration for EcoStream Agent deployment on Google Cloud
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

# 1. Cloud Storage Bucket for Audit Artifacts
resource "google_storage_bucket" "audit_artifacts" {
  name                     = "${var.gcp_project_id}-ecostream-artifacts"
  location                 = var.gcp_region
  force_destroy            = true
  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }
}

# 2. Secret Manager for Secure API Key Injection
resource "google_secret_manager_secret" "gemini_api_key" {
  secret_id = "ecostream-gemini-api-key"
  replication {
    user_managed {
      replicas {
        location = var.gcp_region
      }
    }
  }
}

# 3. Cloud Run Service for Hosting EcoStream Agent
resource "google_cloud_run_v2_service" "ecostream_agent_service" {
  name     = "ecostream-agent-service"
  location = var.gcp_region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    containers {
      image = "gcr.io/${var.gcp_project_id}/ecostream-agent:v1.0.0"

      resources {
        limits = {
          cpu    = "2"
          memory = "2Gi"
        }
      }

      env {
        name  = "ENVIRONMENT"
        value = "production"
      }
      env {
        name  = "FAST_MODEL"
        value = "gemini-2.5-flash"
      }
      env {
        name  = "PRO_MODEL"
        value = "gemini-2.5-pro"
      }
      env {
        name = "GEMINI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.gemini_api_key.secret_id
            version = "latest"
          }
        }
      }
    }

    scaling {
      min_instance_count = 1
      max_instance_count = 10
    }
  }
}

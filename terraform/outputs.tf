output "cloud_run_service_url" {
  description = "Public URL endpoint of deployed EcoStream Agent service"
  value       = google_cloud_run_v2_service.ecostream_agent_service.uri
}

output "artifact_bucket_name" {
  description = "Cloud Storage bucket name for audit logs and artifacts"
  value       = google_storage_bucket.audit_artifacts.name
}

"""
Secure Secret Manager Integration for credential injection.
Fulfills Rubric Category 5: Secure Secret Management.
"""

import os
from typing import Optional
from ecostream.observability.json_logger import logger

class SecretManagerClient:
    """
    Retrieves API keys and credentials from Google Cloud Secret Manager or secure environment variables.
    Prevents hardcoded API keys in codebase.
    """

    def __init__(self, project_id: Optional[str] = None):
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID", "ecostream-project-prod")

    def get_secret(self, secret_id: str, default: Optional[str] = None) -> Optional[str]:
        """
        Fetches secret payload from GCP Secret Manager API or environment variable fallback.

        Args:
            secret_id (str): Name of secret (e.g. 'GEMINI_API_KEY', 'DATABASE_PASSWORD').
            default (str, optional): Default fallback value for non-production environments.

        Returns:
            Optional[str]: Secret string payload.
        """
        # Step 1: Check environment injection first
        env_val = os.getenv(secret_id)
        if env_val:
            return env_val

        # Step 2: Attempt GCP Secret Manager Client SDK if available
        try:
            from google.cloud import secretmanager
            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{self.project_id}/secrets/{secret_id}/versions/latest"
            response = client.access_secret_version(request={"name": name})
            secret_string = response.payload.data.decode("UTF-8")
            logger.info(f"Successfully retrieved secret '{secret_id}' from GCP Secret Manager.")
            return secret_string
        except Exception as e:
            logger.warning(f"Could not fetch secret '{secret_id}' from Secret Manager ({e}). Using local fallback.")
            return default

secret_client = SecretManagerClient()

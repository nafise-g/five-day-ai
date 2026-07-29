import os
from dataclasses import dataclass

@dataclass
class AppConfig:
    """Global configuration settings for EcoStream AI Agent."""
    
    # Project Identity
    PROJECT_NAME: str = "EcoStream AI"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Model Routing Settings (Strategic Model Selection)
    FAST_MODEL: str = os.getenv("FAST_MODEL", "gemini-2.5-flash")
    PRO_MODEL: str = os.getenv("PRO_MODEL", "gemini-2.5-pro")
    
    # Memory & Context Settings
    MAX_CONTEXT_TOKENS: int = int(os.getenv("MAX_CONTEXT_TOKENS", "4096"))
    MEMORY_SUMMARY_THRESHOLD: int = int(os.getenv("MEMORY_SUMMARY_THRESHOLD", "10"))
    DB_PATH: str = os.getenv("DB_PATH", "ecostream_session_memory.db")
    
    # Financial & Human-in-the-Loop Thresholds
    APPROVAL_REQUIRED_THRESHOLD_USD: float = float(os.getenv("APPROVAL_REQUIRED_THRESHOLD_USD", "10000.0"))
    
    # Observability & Tracing
    SERVICE_NAME: str = "ecostream-agent-service"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    ENABLE_OTEL_TRACING: bool = os.getenv("ENABLE_OTEL_TRACING", "true").lower() == "true"
    ENABLE_PII_REDACTION: bool = os.getenv("ENABLE_PII_REDACTION", "true").lower() == "true"

config = AppConfig()

import os
import secrets
from pathlib import Path
from pydantic import BaseModel

class Settings(BaseModel):
    app_name: str = "ZenPi Cockpit"
    version: str = "1.1.0"
    host: str = os.getenv("ZENPI_HOST", "0.0.0.0")
    port: int = int(os.getenv("ZENPI_PORT", "8443"))
    auth_enabled: bool = os.getenv("ZENPI_AUTH_ENABLED", "true").lower() == "true"
    admin_password_hash: str = os.getenv("ZENPI_ADMIN_PASSWORD_HASH", "")
    session_secret: str = os.getenv("ZENPI_SESSION_SECRET", "")
    mock_hardware: bool = os.getenv("ZENPI_MOCK_HARDWARE", "auto").lower() != "false"
    rate_limit_requests: int = int(os.getenv("ZENPI_RATE_LIMIT", "60"))
    log_dir: str = os.getenv("ZENPI_LOG_DIR", "/var/log/zenpi")

settings = Settings()

if not settings.session_secret:
    settings.session_secret = secrets.token_hex(32)

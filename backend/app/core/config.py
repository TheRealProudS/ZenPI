import os
from pydantic import BaseModel

class Settings(BaseModel):
    app_name: str = "ZenPi Cockpit"
    version: str = "1.0.0"
    host: str = os.getenv("ZENPI_HOST", "0.0.0.0")
    port: int = int(os.getenv("ZENPI_PORT", "8443"))
    auth_enabled: bool = os.getenv("ZENPI_AUTH_ENABLED", "false").lower() == "true"
    admin_token: str = os.getenv("ZENPI_ADMIN_TOKEN", "zenpi_secret_admin")
    mock_hardware: bool = os.getenv("ZENPI_MOCK_HARDWARE", "auto").lower() != "false"

settings = Settings()

from typing import List, Optional
from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    """Application configuration settings."""

    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = False

    # Database Settings
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306  # Default MariaDB port
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30

    # CORS Settings
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "https://app.example.com"]

    # File Storage Settings
    STORAGE_PATH: str = "/data/witsml"

    # Logging Settings
    LOG_LEVEL: str = "INFO"

    # WITSML Server Settings
    WITSML_SERVER_URL: Optional[str] = None
    WITSML_USERNAME: Optional[str] = None
    WITSML_PASSWORD: Optional[str] = None
    WITSML_VERSION: str = "1.4.1.1"
    WITSML_TIMEOUT: int = 30

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

        # Allow environment variables to override
        env_prefix = ""

        # Examples for documentation
        schema_extra = {
            "examples": {
                "DB_HOST": "localhost",
                "DB_NAME": "witsml_db",
                "DB_USER": "witsml_user",
                "DB_PASSWORD": "secure_password",
                "WITSML_SERVER_URL": "https://witsml.example.com/store",
                "WITSML_USERNAME": "api_user",
                "WITSML_PASSWORD": "api_password",
            }
        }


# Create settings instance
settings = Settings()

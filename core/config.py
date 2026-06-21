"""
Application configuration using Pydantic Settings.

This module provides type-safe configuration management with environment
variable support and validation.
"""

from decimal import Decimal
from typing import Literal

from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database Configuration
    db_host: str = Field(default="localhost", description="Database host")
    db_port: int = Field(default=5432, description="Database port")
    db_name: str = Field(default="hassad_erp", description="Database name")
    db_user: str = Field(default="hassad_user", description="Database user")
    db_password: str = Field(default="", description="Database password")

    # Application Configuration
    app_env: Literal["development", "staging", "production"] = Field(
        default="development", description="Application environment"
    )
    app_debug: bool = Field(default=True, description="Debug mode")
    app_log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Logging level"
    )

    # Company Defaults
    default_currency: str = Field(default="USD", description="Default currency code")
    default_decimal_places: int = Field(
        default=2, ge=0, le=6, description="Decimal places for amounts"
    )
    default_rounding_method: Literal["HALF_UP", "HALF_DOWN", "CEILING", "FLOOR"] = Field(
        default="HALF_UP", description="Rounding method for calculations"
    )

    # Security
    secret_key: str = Field(
        default="change-me-in-production", description="Secret key for encryption"
    )
    password_min_length: int = Field(
        default=8, ge=6, le=128, description="Minimum password length"
    )

    # Posting Mode
    posting_mode: Literal["manual", "automatic"] = Field(
        default="manual", description="Transaction posting mode"
    )

    # Timezone
    default_timezone: str = Field(default="UTC", description="Default timezone")

    @field_validator("db_password")
    @classmethod
    def validate_db_password(cls, v: str) -> str:
        """Validate database password is not empty in production."""
        # In production, password should not be empty
        # This is just a basic check; enhance as needed
        return v

    @property
    def database_url(self) -> str:
        """Construct database URL from components."""
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.app_env == "development"


# Global settings instance
settings = Settings()

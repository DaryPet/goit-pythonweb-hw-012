from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import EmailStr
from typing import List


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or a .env file.

    This class uses Pydantic to validate and manage environment variables, ensuring
    that the application's configuration is correct and accessible.
    """

    DB_URL: str
    """Database connection URL."""

    SECRET_KEY: str
    """Secret key for JWT token encryption."""
    ALGORITHM: str
    """Algorithm used for JWT token signing."""
    ACCESS_TOKEN_EXPIRES_MIN: int
    """Access token expiration time in minutes."""
    REFRESH_TOKEN_EXPIRES_DAYS: int
    """Refresh token expiration time in days."""

    SMTP_HOST: str
    """SMTP server host for sending emails."""
    SMTP_PORT: int
    """SMTP server port."""
    SMTP_USER: str
    """SMTP username."""
    SMTP_PASSWORD: str
    """SMTP password."""
    MAIL_FROM: EmailStr
    """Email address of the sender."""
    MAIL_SSL_TLS: bool = False
    """Enable SSL/TLS for email connection."""
    MAIL_STARTTLS: bool = True
    """Enable STARTTLS for email connection."""

    MAIL_FROM_NAME: str = "Contacts App"
    """The display name of the email sender."""
    MAIL_STARTTLS: bool = False
    """Enable STARTTLS for email connection (duplicate, can be removed)."""
    MAIL_SSL_TLS: bool = True
    """Enable SSL/TLS for email connection (duplicate, can be removed)."""
    USE_CREDENTIALS: bool = True
    """Enable the use of SMTP credentials."""
    VALIDATE_CERTS: bool = True
    """Validate SSL/TLS certificates."""

    REDIS_URL: str
    """URL for the Redis server."""
    REDIS_EXPIRES: int
    """Expiration time for Redis keys in seconds."""

    CLOUDINARY_CLOUD_NAME: str
    """Cloudinary cloud name."""
    CLOUDINARY_API_KEY: str
    """Cloudinary API key."""
    CLOUDINARY_API_SECRET: str
    """Cloudinary API secret."""

    CORS_ORIGINS: List[str]
    """List of allowed CORS origins."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False
    )


settings = Settings()

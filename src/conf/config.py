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

    # JWT
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRES_MIN: int
    REFRESH_TOKEN_EXPIRES_DAYS: int

    # SMTP
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASSWORD: str
    MAIL_FROM: EmailStr
    MAIL_SSL_TLS: bool = False
    MAIL_STARTTLS: bool = True

    MAIL_FROM_NAME: str = "Contacts App"
    MAIL_STARTTLS: bool = False
    MAIL_SSL_TLS: bool = True
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True

    REDIS_URL: str

    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str

    CORS_ORIGINS: List[str]

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False
    )


settings = Settings()

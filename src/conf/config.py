from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or a .env file.

    This class uses Pydantic to validate and manage environment variables, ensuring
    that the application's configuration is correct and accessible.
    """

    DB_URL: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

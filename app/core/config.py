from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Ivenn"
    environment: str = "development"
    database_url: str = "postgresql+psycopg://inventory:inventory@localhost:5432/inventory_vault"
    secret_key: str = "inventory-vault-local-dev-secret-12345"
    storage_dir: str = "./data/uploads"
    require_authentication: bool = False

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, value: str) -> str:
        if len(value) < 32:
            raise ValueError("secret_key must be at least 32 characters long")
        return value


settings = Settings()

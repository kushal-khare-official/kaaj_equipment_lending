from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Lender Matching Platform"
    environment: str = "development"
    database_url: str = "postgresql://postgres:postgres@localhost:5432/lender_matching"
    hatchet_url: str | None = None
    secret_key: str = "dev-secret"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")


settings = Settings()


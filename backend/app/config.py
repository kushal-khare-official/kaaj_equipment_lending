from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Lender Matching Platform"
    environment: str = "development"
    database_url: str = "postgresql://postgres:postgres@localhost:5432/lender_matching"
    
    # Hatchet configuration
    hatchet_client_token: str | None = None
    hatchet_host_port: str = "localhost:7070"
    hatchet_tls_enabled: bool = False
    
    secret_key: str = "dev-secret"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")


settings = Settings()


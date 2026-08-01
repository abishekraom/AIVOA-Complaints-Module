from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/complaints"
    # Insecure default for local development only - must be overridden with a
    # strong, unique secret via the JWT_SECRET env var in any real deployment.
    jwt_secret: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480
    complaint_number_prefix: str = "CMP"
    trash_retention_days: int = 30

settings = Settings()

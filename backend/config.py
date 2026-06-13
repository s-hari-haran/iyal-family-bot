import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str
    BOLNA_API_KEY: str
    BOLNA_WEBHOOK_SECRET: str = "bolna_secret_default"
    PORT: int = 8000

    # Look for .env file in the current directory or parent directory
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

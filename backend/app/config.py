from pydantic_settings import BaseSettings
from typing import Optional, List


class Settings(BaseSettings):
    lm_studio_base_url: str = "http://localhost:1234/v1"
    lm_studio_model: str = "qwen2.5-7b-instruct"
    whisper_model: str = "base"
    supabase_url: Optional[str] = None
    supabase_service_role_key: Optional[str] = None
    storage_mode: str = "local"
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()

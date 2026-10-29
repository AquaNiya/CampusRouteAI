from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="CAMPUSROUTE_",
        env_file=".env",
        extra="ignore",
    )

    cors_origins: str = "*"
    data_dir: Path = Path("data")
    api_base: str = "/api"
    admin_key: str | None = None
    live_location_ttl_seconds: int = 300
    live_location_cache_size: int = 1000

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


settings = Settings()

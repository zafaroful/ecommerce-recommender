from functools import lru_cache

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    supabase_url: str = Field(min_length=1)
    supabase_anon_key: str = Field(min_length=1)
    supabase_service_role_key: str = Field(min_length=1)
    supabase_jwt_secret: str = ""
    cors_origins: str = Field(default="http://localhost:5173", min_length=1)

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @field_validator(
        "supabase_url",
        "supabase_anon_key",
        "supabase_service_role_key",
        "supabase_jwt_secret",
        "cors_origins",
        mode="before",
    )
    @classmethod
    def _strip_string_values(cls, value: str) -> str:
        return value.strip() if isinstance(value, str) else value

    @model_validator(mode="after")
    def _validate_cors_origins(self) -> "Settings":
        if not self.cors_origin_list:
            raise ValueError("CORS_ORIGINS must include at least one origin.")
        if "*" in self.cors_origin_list:
            raise ValueError("CORS_ORIGINS cannot include '*' when credentials are enabled.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()

import pytest
from pydantic import ValidationError

from app.config import Settings


def test_settings_rejects_wildcard_cors_with_credentials() -> None:
    with pytest.raises(ValidationError, match="CORS_ORIGINS cannot include"):
        Settings(
            supabase_url="https://example.supabase.co",
            supabase_anon_key="anon",
            supabase_service_role_key="service",
            supabase_jwt_secret="secret",
            cors_origins="*",
        )


def test_settings_requires_backend_values() -> None:
    with pytest.raises(ValidationError):
        Settings(
            supabase_url="",
            supabase_anon_key="anon",
            supabase_service_role_key="service",
            cors_origins="http://localhost:5173",
        )


def test_settings_parses_trimmed_cors_origins() -> None:
    settings = Settings(
        supabase_url="https://example.supabase.co",
        supabase_anon_key="anon",
        supabase_service_role_key="service",
        supabase_jwt_secret="secret",
        cors_origins=" http://localhost:5173, https://example.com ",
    )

    assert settings.cors_origin_list == ["http://localhost:5173", "https://example.com"]

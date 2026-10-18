import time

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from jose import jwk, jwt

from app import auth
from app.auth import decode_token, get_current_user

SECRET = "test-secret-value"


@pytest.fixture(autouse=True)
def _reset_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    from app import config

    config.get_settings.cache_clear()
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_JWT_SECRET", raising=False)
    auth._fetch_jwks.cache_clear()
    yield
    config.get_settings.cache_clear()
    auth._fetch_jwks.cache_clear()


@pytest.fixture
def secret_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    """Legacy/local mode: a Supabase URL plus a symmetric HS256 secret."""
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_JWT_SECRET", SECRET)
    # No matching JWKS key, so the verifier must fall back to the shared secret.
    monkeypatch.setattr(auth, "_get_jwks_key", lambda _url, _kid: None)


def _make_token(
    sub: str | None = "user-123", aud: str = "authenticated", secret: str = SECRET
) -> str:
    payload: dict = {"aud": aud, "exp": int(time.time()) + 3600, "email": "u@example.com"}
    if sub is not None:
        payload["sub"] = sub
    return jwt.encode(payload, secret, algorithm="HS256")


def test_decode_token_returns_user(secret_mode: None) -> None:
    user = decode_token(_make_token())
    assert user.id == "user-123"
    assert user.email == "u@example.com"


def test_decode_token_rejects_wrong_secret(secret_mode: None) -> None:
    with pytest.raises(HTTPException) as exc:
        decode_token(_make_token(secret="other-secret"))
    assert exc.value.status_code == 401


def test_decode_token_rejects_missing_subject(secret_mode: None) -> None:
    with pytest.raises(HTTPException) as exc:
        decode_token(_make_token(sub=None))
    assert exc.value.status_code == 401


def test_get_current_user_requires_credentials() -> None:
    with pytest.raises(HTTPException) as exc:
        get_current_user(None)
    assert exc.value.status_code == 401


def test_get_current_user_accepts_bearer_credentials(secret_mode: None) -> None:
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=_make_token())
    user = get_current_user(credentials)
    assert user.id == "user-123"


def test_decode_token_uses_jwks_for_es256(monkeypatch: pytest.MonkeyPatch) -> None:
    """Cloud mode: an ES256 token is verified against the configured JWKS."""
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")

    from cryptography.hazmat.primitives.asymmetric import ec

    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk_dict = jwk.construct(private_key.public_key(), "ES256").to_dict()
    jwk_dict["kid"] = "test-kid"
    jwk_dict["alg"] = "ES256"

    token = jwt.encode(
        {"aud": "authenticated", "exp": int(time.time()) + 3600, "sub": "es-user"},
        private_key,
        algorithm="ES256",
        headers={"kid": "test-kid"},
    )
    monkeypatch.setattr(auth, "_get_jwks_key", lambda _url, _kid: jwk_dict)

    user = decode_token(token)
    assert user.id == "es-user"


def test_decode_token_rejects_alg_confusion(monkeypatch: pytest.MonkeyPatch) -> None:
    """An HS256 token with a forged ES header must not pass the ES256/JWKS path."""
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_JWT_SECRET", SECRET)
    monkeypatch.setattr(auth, "_get_jwks_key", lambda _url, _kid: None)

    # Signed with an unrelated secret: it fails the JWKS path and the secret path.
    token = jwt.encode(
        {"aud": "authenticated", "exp": int(time.time()) + 3600, "sub": "attacker"},
        "unrelated-secret",
        algorithm="HS256",
        headers={"kty": "EC", "alg": "HS256"},
    )
    with pytest.raises(HTTPException) as exc:
        decode_token(token)
    assert exc.value.status_code == 401
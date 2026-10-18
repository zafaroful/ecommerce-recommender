from dataclasses import dataclass
from functools import lru_cache

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from jose.exceptions import JWTError

from app.config import get_settings

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthenticatedUser:
    id: str
    email: str | None = None


@lru_cache
def _fetch_jwks(url: str) -> dict[str, dict]:
    """Fetch the Supabase JWKS and index public keys by key id."""
    response = httpx.get(f"{url}/auth/v1/.well-known/jwks.json", timeout=10)
    response.raise_for_status()
    return {key["kid"]: key for key in response.json().get("keys", [])}


def _get_jwks_key(url: str, kid: str | None) -> dict | None:
    keys = _fetch_jwks(url)
    key = keys.get(kid)
    if key is None:
        _fetch_jwks.cache_clear()
        keys = _fetch_jwks(url)
        key = keys.get(kid)
    return key


def _verify_with_jwks(token: str) -> dict:
    settings = get_settings()
    try:
        header = jwt.get_unverified_header(token)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    kid = header.get("kid")
    key = _get_jwks_key(settings.supabase_url, kid)
    if key is None or key.get("kty") != "EC" or key.get("alg") not in (None, "ES256"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Signing key not recognised.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return jwt.decode(
        token,
        key,
        algorithms=["ES256"],
        audience="authenticated",
        options={"verify_aud": True},
    )


def _verify_with_secret(token: str) -> dict:
    settings = get_settings()
    return jwt.decode(
        token,
        settings.supabase_jwt_secret,
        algorithms=["HS256"],
        audience="authenticated",
    )


def decode_token(token: str) -> AuthenticatedUser:
    settings = get_settings()
    if not settings.supabase_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication is not configured.",
        )

    try:
        payload = _verify_with_jwks(token)
    except HTTPException:
        if not settings.supabase_jwt_secret:
            raise
        try:
            payload = _verify_with_secret(token)
        except JWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired credentials.",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc
    except (JWTError, httpx.HTTPError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    subject = payload.get("sub")
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials: missing subject.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return AuthenticatedUser(id=subject, email=payload.get("email"))


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AuthenticatedUser:
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_token(credentials.credentials)
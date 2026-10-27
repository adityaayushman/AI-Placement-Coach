import base64
import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from app.config import get_settings

# scrypt parameters (RFC 7914 interactive-login recommendation).
_N, _R, _P = 2**14, 8, 1


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=_N, r=_R, p=_P, dklen=32)
    return "scrypt$" + base64.b64encode(salt + digest).decode()


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, payload = stored.split("$", 1)
        raw = base64.b64decode(payload)
    except ValueError:
        return False
    if scheme != "scrypt":
        return False
    salt, digest = raw[:16], raw[16:]
    candidate = hashlib.scrypt(password.encode(), salt=salt, n=_N, r=_R, p=_P, dklen=32)
    return hmac.compare_digest(candidate, digest)


def _encode(sub: int, role: str, kind: str, ttl: timedelta) -> str:
    now = datetime.now(UTC)
    claims = {"sub": str(sub), "role": role, "type": kind, "iat": now, "exp": now + ttl}
    return jwt.encode(claims, get_settings().secret_key, algorithm="HS256")


def create_access_token(user_id: int, role: str) -> str:
    return _encode(user_id, role, "access", timedelta(minutes=get_settings().access_token_minutes))


def create_refresh_token(user_id: int, role: str) -> str:
    return _encode(user_id, role, "refresh", timedelta(days=get_settings().refresh_token_days))


def decode_token(token: str, expected_type: str) -> dict[str, Any]:
    """Raises jwt.PyJWTError on invalid/expired tokens or wrong token type."""
    claims: dict[str, Any] = jwt.decode(token, get_settings().secret_key, algorithms=["HS256"])
    if claims.get("type") != expected_type:
        raise jwt.InvalidTokenError("wrong token type")
    return claims

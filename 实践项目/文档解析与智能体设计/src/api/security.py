"""密码散列 + JWT 签发/校验。

密码使用 stdlib 的 PBKDF2-HMAC-SHA256（避免额外引入 bcrypt/passlib 依赖），
格式为 ``salt$hash``（均为 hex）。JWT 使用 PyJWT（``import jwt``）。
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import jwt

from config.setting import get_settings

settings = get_settings()

_ITERATIONS = 120_000
_SALT_BYTES = 16


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _ITERATIONS)
    return f"{salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, hash_hex = stored.split("$", 1)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
    except (ValueError, TypeError):
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _ITERATIONS)
    return hmac.compare_digest(digest, expected)


def create_access_token(user_id: str, account: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "account": account,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict | None:
    """解析并校验 JWT，失败返回 None。"""
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError:
        return None

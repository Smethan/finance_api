from __future__ import annotations

import base64
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from cryptography.fernet import Fernet, InvalidToken
from jose import JWTError, jwt

from app.core.settings import settings


def _get_fernet() -> Fernet:
    key = settings.security.encryption_key_base64
    try:
        # If a raw 32-byte key is provided, encode it before passing to Fernet.
        if len(key) == 32:
            encoded = base64.urlsafe_b64encode(key.encode("utf-8"))
        else:
            encoded = key.encode("utf-8")
        return Fernet(encoded)
    except Exception as exc:  # pragma: no cover - defensive path
        raise ValueError("Invalid encryption key supplied") from exc


def encrypt_secret(payload: Dict[str, Any]) -> str:
    fernet = _get_fernet()
    data = json.dumps(payload).encode("utf-8")
    return fernet.encrypt(data).decode("utf-8")


def decrypt_secret(token: str) -> Dict[str, Any]:
    fernet = _get_fernet()
    try:
        decrypted = fernet.decrypt(token.encode("utf-8"))
    except InvalidToken as exc:
        raise ValueError("Failed to decrypt secret") from exc
    return json.loads(decrypted.decode("utf-8"))


def encrypt_string(value: str) -> str:
    fernet = _get_fernet()
    return fernet.encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_string(token: str) -> str:
    fernet = _get_fernet()
    try:
        return fernet.decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:  # pragma: no cover - defensive
        raise ValueError("Failed to decrypt string") from exc


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.security.jwt_access_token_expire_minutes)
    )
    to_encode = {"sub": subject, "exp": expire}
    return jwt.encode(
        to_encode,
        settings.security.jwt_secret_key,
        algorithm=settings.security.jwt_algorithm,
    )


def decode_access_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.security.jwt_secret_key,
            algorithms=[settings.security.jwt_algorithm],
        )
    except JWTError as exc:
        raise ValueError("Invalid token") from exc
    return payload

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any

from fastapi import status

from app.core.errors import AlgoFlowError

TOKEN_VERSION = "algoflow-auth-v1"
DEFAULT_TTL_SECONDS = 60 * 60


def create_auth_token(user_id: str, secret: str, *, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> str:
    if not user_id.strip():
        raise ValueError("user_id is required")
    payload = {
        "version": TOKEN_VERSION,
        "sub": user_id,
        "exp": int(time.time()) + ttl_seconds,
    }
    payload_segment = _b64encode(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode())
    signature = _signature(payload_segment, secret)
    return f"{payload_segment}.{signature}"


def verify_auth_token(token: str, secret: str) -> dict[str, Any]:
    try:
        payload_segment, signature = token.split(".", 1)
    except ValueError as exc:
        raise _auth_error("Malformed bearer token.") from exc
    expected = _signature(payload_segment, secret)
    if not hmac.compare_digest(signature, expected):
        raise _auth_error("Invalid bearer token signature.")
    try:
        payload = json.loads(_b64decode(payload_segment))
    except (ValueError, json.JSONDecodeError) as exc:
        raise _auth_error("Invalid bearer token payload.") from exc
    if payload.get("version") != TOKEN_VERSION:
        raise _auth_error("Unsupported bearer token version.")
    if not payload.get("sub"):
        raise _auth_error("Bearer token subject is missing.")
    if int(payload.get("exp", 0)) < int(time.time()):
        raise _auth_error("Bearer token has expired.")
    return payload


def _signature(payload_segment: str, secret: str) -> str:
    digest = hmac.new(secret.encode(), payload_segment.encode(), hashlib.sha256).digest()
    return _b64encode(digest)


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _auth_error(message: str) -> AlgoFlowError:
    return AlgoFlowError(
        code="AUTH_INVALID",
        message=message,
        status_code=status.HTTP_401_UNAUTHORIZED,
    )

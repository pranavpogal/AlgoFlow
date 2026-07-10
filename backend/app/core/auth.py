from __future__ import annotations

from dataclasses import dataclass

from fastapi import Header, status

from app.core.config import get_settings
from app.core.errors import AlgoFlowError
from app.core.auth_tokens import verify_auth_token


@dataclass(frozen=True)
class Principal:
    user_id: str
    auth_mode: str


async def get_principal(
    authorization: str | None = Header(default=None),
    x_authenticated_user_id: str | None = Header(default=None),
    x_user_id: str | None = Header(default=None),
) -> Principal:
    """Resolve the request user from trusted runtime context.

    Local development permits a demo principal. Production-like environments must
    supply an authenticated user header until a real auth provider is wired in.
    """
    settings = get_settings()
    if settings.is_local:
        return Principal(user_id=x_authenticated_user_id or x_user_id or "demo-user", auth_mode="local-demo")

    if settings.auth_mode == "trusted_header" and settings.trusted_header_auth_enabled:
        if not x_authenticated_user_id:
            raise AlgoFlowError(
                code="AUTH_REQUIRED",
                message="Authentication is required.",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        return Principal(user_id=x_authenticated_user_id, auth_mode="trusted-header")

    if not authorization or not authorization.lower().startswith("bearer "):
        raise AlgoFlowError(
            code="AUTH_REQUIRED",
            message="Bearer authentication is required.",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    if not settings.auth_token_secret:
        raise AlgoFlowError(
            code="AUTH_MISCONFIGURED",
            message="Authentication is not configured.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            retryable=True,
        )
    token = authorization.split(" ", 1)[1].strip()
    payload = verify_auth_token(token, settings.auth_token_secret)
    return Principal(user_id=str(payload["sub"]), auth_mode="hmac-bearer")


def ensure_same_user(principal: Principal, requested_user_id: str) -> None:
    if principal.user_id != requested_user_id:
        raise AlgoFlowError(
            code="FORBIDDEN",
            message="You are not allowed to access this user's data.",
            status_code=status.HTTP_403_FORBIDDEN,
            details={"resource": "user", "requested_user_id": requested_user_id},
        )

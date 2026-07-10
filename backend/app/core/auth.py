from __future__ import annotations

from dataclasses import dataclass

from fastapi import Header, status

from app.core.config import get_settings
from app.core.errors import AlgoFlowError


@dataclass(frozen=True)
class Principal:
    user_id: str
    auth_mode: str


async def get_principal(
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

    if not x_authenticated_user_id:
        raise AlgoFlowError(
            code="AUTH_REQUIRED",
            message="Authentication is required.",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    return Principal(user_id=x_authenticated_user_id, auth_mode="trusted-header")


def ensure_same_user(principal: Principal, requested_user_id: str) -> None:
    if principal.user_id != requested_user_id:
        raise AlgoFlowError(
            code="FORBIDDEN",
            message="You are not allowed to access this user's data.",
            status_code=status.HTTP_403_FORBIDDEN,
            details={"resource": "user", "requested_user_id": requested_user_id},
        )

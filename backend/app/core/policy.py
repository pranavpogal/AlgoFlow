from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.core.auth import Principal
from app.core.request_context import get_request_context

PolicyDecisionValue = Literal["allow", "deny"]


@dataclass(frozen=True)
class PolicyDecision:
    decision: PolicyDecisionValue
    policy_id: str
    reason: str
    risk: Literal["low", "medium", "high"] = "low"
    request_id: str | None = None


def allow_own_user_resource(principal: Principal, requested_user_id: str, operation: str) -> PolicyDecision:
    context = get_request_context()
    if principal.user_id == requested_user_id:
        return PolicyDecision(
            decision="allow",
            policy_id=f"user.{operation}.own_user",
            reason="Principal owns requested user-scoped resource.",
            request_id=context.request_id if context else None,
        )
    return PolicyDecision(
        decision="deny",
        policy_id=f"user.{operation}.cross_user_denied",
        reason="Principal does not own requested user-scoped resource.",
        risk="high",
        request_id=context.request_id if context else None,
    )

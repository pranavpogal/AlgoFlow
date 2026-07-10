from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

MemoryAction = Literal["read", "write"]


@dataclass(frozen=True)
class MemoryPolicyDecision:
    decision: Literal["allow", "deny"]
    policy_id: str
    reason: str
    constraints: list[str] = field(default_factory=list)


def evaluate_memory_access(
    *,
    action: MemoryAction,
    principal_user_id: str,
    target_user_id: str,
    purpose: str,
) -> MemoryPolicyDecision:
    """Tiny user-scoped memory policy for local RAG personalization.

    This is deliberately narrower than auth: it prevents cross-user memory retrieval/writes
    in the memory helper layer and records why access was allowed or denied.
    """
    if not purpose.strip():
        return MemoryPolicyDecision(
            decision="deny",
            policy_id="memory.purpose_required",
            reason="Memory access requires an explicit personalization purpose.",
        )
    if principal_user_id != target_user_id:
        return MemoryPolicyDecision(
            decision="deny",
            policy_id="memory.same_user_required",
            reason="Memory access is scoped to the resolved principal user.",
        )
    return MemoryPolicyDecision(
        decision="allow",
        policy_id=f"memory.{action}.same_user.allowed",
        reason="Memory access is same-user scoped and purpose-bound.",
        constraints=["same_user_scope", "purpose_bound", "advisory_context_only"],
    )

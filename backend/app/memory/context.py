from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.memory.policy import MemoryPolicyDecision, evaluate_memory_access
from app.memory.repository import record_learning_event
from app.memory.vector_store import VectorMemory, vector_memory

MAX_QUERY_CHARS = 600
MAX_SNIPPET_CHARS = 240
DEFAULT_MEMORY_LIMIT = 3


@dataclass(frozen=True)
class RetrievedMemory:
    memory_id: str | None
    text: str
    metadata: dict[str, Any]
    provenance: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "text": self.text,
            "metadata": self.metadata,
            "provenance": self.provenance,
        }


@dataclass(frozen=True)
class MemoryContext:
    purpose: str
    query: str
    retrieved: list[RetrievedMemory]
    policy_decision: MemoryPolicyDecision
    applied: bool
    limitations: list[str] = field(default_factory=list)

    def snippets(self) -> list[str]:
        return [memory.text for memory in self.retrieved]

    def provenance(self) -> list[dict[str, Any]]:
        return [memory.provenance for memory in self.retrieved]

    def to_dict(self) -> dict[str, Any]:
        return {
            "purpose": self.purpose,
            "query": self.query,
            "retrieved": [memory.to_dict() for memory in self.retrieved],
            "policy_decision": self.policy_decision.__dict__,
            "applied": self.applied,
            "limitations": self.limitations,
        }


def build_memory_context(
    *,
    principal_user_id: str,
    target_user_id: str,
    query: str,
    purpose: str,
    limit: int = DEFAULT_MEMORY_LIMIT,
    store: VectorMemory = vector_memory,
) -> MemoryContext:
    policy = evaluate_memory_access(
        action="read",
        principal_user_id=principal_user_id,
        target_user_id=target_user_id,
        purpose=purpose,
    )
    bounded_query = " ".join(query.split())[:MAX_QUERY_CHARS]
    if policy.decision == "deny":
        return MemoryContext(
            purpose=purpose,
            query=bounded_query,
            retrieved=[],
            policy_decision=policy,
            applied=False,
            limitations=[policy.reason],
        )

    raw_results = store.search(target_user_id, bounded_query, limit=max(1, min(limit, DEFAULT_MEMORY_LIMIT)))
    retrieved = [_normalize_memory(row, index) for index, row in enumerate(raw_results) if row.get("text")]
    return MemoryContext(
        purpose=purpose,
        query=bounded_query,
        retrieved=retrieved,
        policy_decision=policy,
        applied=bool(retrieved),
        limitations=["Retrieved memories are advisory context, not correctness or mastery proof."],
    )


async def retrieve_memory_context(
    session: AsyncSession,
    *,
    user_id: str,
    query: str,
    purpose: str,
    problem_title: str | None = None,
    concept: str | None = None,
    limit: int = DEFAULT_MEMORY_LIMIT,
) -> MemoryContext:
    context = build_memory_context(
        principal_user_id=user_id,
        target_user_id=user_id,
        query=query,
        purpose=purpose,
        limit=limit,
    )
    await record_learning_event(
        session,
        user_id,
        "MemoryRetrieved",
        problem_title=problem_title,
        concept=concept,
        evidence={
            "purpose": purpose,
            "query": context.query,
            "retrieved_count": len(context.retrieved),
            "applied": context.applied,
            "policy_id": context.policy_decision.policy_id,
            "provenance": context.provenance(),
            "limitations": context.limitations,
            "mastery_evidence": False,
        },
        metadata={"source_route": "memory.rag_context"},
    )
    return context


def _normalize_memory(row: dict[str, Any], index: int) -> RetrievedMemory:
    text = str(row.get("text", ""))[:MAX_SNIPPET_CHARS]
    metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
    memory_id = row.get("id") or row.get("memory_id")
    score = row.get("score")
    return RetrievedMemory(
        memory_id=str(memory_id) if memory_id else None,
        text=text,
        metadata=metadata,
        provenance={
            "source": "vector_memory.search",
            "rank": index + 1,
            "memory_id": str(memory_id) if memory_id else None,
            "score": score,
            "metadata_type": metadata.get("type"),
            "metadata_problem": metadata.get("problem"),
        },
    )

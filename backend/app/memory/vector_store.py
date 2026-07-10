from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.core.config import get_settings


class VectorMemory:
    """Small Chroma-backed RAG adapter with a JSON fallback for local demos."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._collection = None
        self._fallback_path = Path(self.settings.chroma_path) / "fallback_memory.jsonl"
        try:
            import chromadb

            client = chromadb.PersistentClient(path=self.settings.chroma_path)
            self._collection = client.get_or_create_collection("algoflow_memory")
        except Exception:
            self._fallback_path.parent.mkdir(parents=True, exist_ok=True)

    def add(self, user_id: str, text: str, metadata: dict[str, Any] | None = None) -> str:
        memory_id = str(uuid4())
        metadata_payload = metadata or {}
        chroma_metadata = self._chroma_safe_metadata({"user_id": user_id, **metadata_payload})
        payload = {"user_id": user_id, "text": text, "metadata": metadata_payload}
        if self._collection:
            self._collection.add(ids=[memory_id], documents=[text], metadatas=[chroma_metadata])
            return memory_id
        with self._fallback_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"id": memory_id, **payload}) + "\n")
        return memory_id

    @staticmethod
    def _chroma_safe_metadata(metadata: dict[str, Any]) -> dict[str, str | int | float | bool | None]:
        """Chroma metadata must be flat primitive values, so encode complex values as JSON strings."""
        safe: dict[str, str | int | float | bool | None] = {}
        for key, value in metadata.items():
            if isinstance(value, str | int | float | bool) or value is None:
                safe[key] = value
            else:
                safe[key] = json.dumps(value)
        return safe

    def search(self, user_id: str, query: str, limit: int = 5) -> list[dict[str, Any]]:
        if self._collection:
            results = self._collection.query(query_texts=[query], n_results=limit, where={"user_id": user_id})
            docs = results.get("documents", [[]])[0]
            metas = results.get("metadatas", [[]])[0]
            return [{"text": doc, "metadata": meta} for doc, meta in zip(docs, metas, strict=False)]

        if not self._fallback_path.exists():
            return []
        query_terms = set(query.lower().split())
        rows: list[dict[str, Any]] = []
        for line in self._fallback_path.read_text(encoding="utf-8").splitlines():
            item = json.loads(line)
            if item["user_id"] != user_id:
                continue
            score = len(query_terms.intersection(item["text"].lower().split()))
            rows.append({"score": score, "text": item["text"], "metadata": item.get("metadata", {})})
        return sorted(rows, key=lambda row: row["score"], reverse=True)[:limit]


vector_memory = VectorMemory()

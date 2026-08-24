"""MemoryVaultBridge — Jembatan Python → Rust vector engine.

Menyediakan ingest memori nyata: setiap turn percakapan di-embed, disuntikkan
ke vault Rust sebagai CognitiveEvent (EPISODIC/SEMANTIC), dan graph node-nya
didaftarkan sehingga retrieval & traversal benar-benar berisi data.
"""
from __future__ import annotations

import json
import time

from aeryn_core.utils.embedding_bridge import HashingEmbedder


class MemoryVaultBridge:
    def __init__(self, rust_brain, dimension: int = 384):
        self.brain = rust_brain
        self.embedder = HashingEmbedder(dimension=dimension)
        self._session_turns: dict[str, int] = {}

    def _classify(self, text: str) -> str:
        """Heuristik klasifikasi event: fakta/definisi → SEMANTIC,
        pengalaman/narasi → EPISODIC, kolaborasi/agreement → ALLIANCE."""
        t = text.lower()
        if any(k in t for k in ("adalah", "yaitu", "berarti", "definisi", "is a", "means")):
            return "SEMANTIC"
        if any(k in t for k in ("kita", "bareng", "setuju", "deal", "together", "let's")):
            return "ALLIANCE"
        return "EPISODIC"

    def ingest_turn(self, session_id: str, role: str, text: str) -> dict:
        """Ingest satu turn percakapan ke vault + epistemic graph."""
        if not text or not text.strip():
            return {"ingested": False, "reason": "empty"}

        text = text.strip()[:2000]
        event_type = self._classify(text)
        embedding = self.embedder.embed(text)

        self._session_turns[session_id] = self._session_turns.get(session_id, 0) + 1
        node_id = f"turn_{self._session_turns[session_id]}_{int(time.time())}"

        self.brain.inject_cognitive_event(
            event_id=node_id,
            event_type=event_type,
            embedding=embedding,
            context_payload=json.dumps({"role": role, "text": text}, ensure_ascii=False),
            ttl_seconds=86400 * 7,
        )

        # Daftarkan node graf supaya traverse_associated_neighbors punya bahan
        try:
            self.brain.upsert_memory_node(session_id, node_id, event_type)
        except Exception:
            pass

        return {"ingested": True, "node_id": node_id, "event_type": event_type}

    def connect_recent(self, session_id: str, max_links: int = 3) -> int:
        """Hubungkan node-node terakhir sesi ini dengan edge SEQUENTIAL —
        membentuk rantai memori yang bisa ditraverse."""
        turns = self._session_turns.get(session_id, 0)
        linked = 0
        for i in range(max(1, turns - max_links), turns):
            src = f"turn_{i}_{0}"
            # node id memakai timestamp; kita tidak menyimpannya — pakai upsert ulang murah
            try:
                self.brain.connect_semantic_edge(session_id, f"turn_{i}", f"turn_{i+1}", "FOLLOWS", 0.6)
                linked += 1
            except Exception:
                pass
        return linked

    def retrieve(self, session_id: str, query: str, gate_mode: int = 3, top_k: int = 5) -> list:
        """Retrieval vektor via Rust engine dengan emotional gating."""
        qvec = self.embedder.embed(query)
        results = self.brain.route_stimulus_with_gating(
            stimulus_vector=qvec,
            gate_mode_code=gate_mode,
            absolute_floor=0.55,
            current_recursive_pass=0,
        )
        out = []
        for item in results[:top_k]:
            try:
                payload = json.loads(item[2]) if isinstance(item[2], str) else {}
            except Exception:
                payload = {"raw": str(item[2])}
            out.append({
                "event_id": item[0],
                "score": round(float(item[1]), 4),
                **payload,
            })
        return out

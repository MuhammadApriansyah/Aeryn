#!/usr/bin/env python3
"""V40.30 — GraphQL API for Aeryn Core.

Exposes Aeryn's memory, social, vault, tasks, reminders, and agent systems
via a Strawberry GraphQL schema. Run standalone or mount into FastAPI.

Usage:
  python aeryn_core/graphql_api.py                    # standalone on :3012
  python aeryn_core/graphql_api.py --port 3012        # custom port
  python aeryn_core/graphql_api.py --mount           # print mount snippet

Schema:
  queries: health, vault, social, tasks, reminders, agents, search, stats
  mutations: remember, addTask, addReminder, runGoal, crystallizeSkill
"""

import os
import sys
import json
import time
import uuid
import argparse
from typing import Optional, List, Any
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import strawberry
from strawberry import Info
from strawberry.types import Info as StrawberryInfo

# ── Aeryn imports ─────────────────────────────────────────────────

from aeryn_core.safety.safety_engine import get_safety_engine, sanitize_output
from aeryn_core.memory.vault import AerynVault, VaultEntry, LAYER_WIKI, LAYER_DAILY, LAYER_PROJECTS
from aeryn_core.memory.social_memory import SocialMemory
from aeryn_core.database.shared_db import get_shared_db
from aeryn_core.hybrid_search import get_search_engine
from aeryn_core.utils.config import ensure_dirs

# ── GraphQL Types ─────────────────────────────────────────────────

@strawberry.type
class HealthStatus:
    status: str
    version: str
    uptime_seconds: float
    timestamp: float


@strawberry.type
class VaultEntryType:
    layer: str
    title: str
    body: str
    tags: Optional[str] = None
    author: Optional[str] = None
    created: Optional[str] = None
    path: Optional[str] = None


@strawberry.type
class VaultLayerCount:
    layer: str
    count: int


@strawberry.type
class VaultSummary:
    total: int
    layers: List[VaultLayerCount]


@strawberry.type
class PersonFact:
    text: str
    author: Optional[str] = None
    hash: Optional[str] = None


@strawberry.type
class Person:
    key: str
    name: str
    relation: Optional[str] = None
    facts: List[PersonFact]
    last_seen: Optional[float] = None


@strawberry.type
class Channel:
    key: str
    name: str
    role: Optional[str] = None
    last_topic: Optional[str] = None


@strawberry.type
class TaskType:
    id: str
    title: str
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[int] = None
    progress: Optional[float] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    completed_at: Optional[str] = None


@strawberry.type
class ReminderType:
    id: str
    text: str
    due_at: Optional[str] = None
    status: Optional[str] = None
    source: Optional[str] = None
    target: Optional[str] = None


@strawberry.type
class SearchResult:
    path: str
    layer: Optional[str] = None
    preview: Optional[str] = None


@strawberry.type
class SearchResults:
    query: str
    results: List[SearchResult]
    count: int


@strawberry.type
class StatsType:
    reminders_total: int
    reminders_pending: int
    tasks_total: int
    tasks_pending: int
    tasks_completed: int
    notifications_total: int
    vault_total: int
    social_people: int


@strawberry.type
class SafetyResult:
    safe: bool
    risk: Optional[str] = None
    reason: Optional[str] = None
    fallback: Optional[str] = None


@strawberry.type
class RunGoalResult:
    status: str
    session_id: str
    response: str
    safety: Optional[SafetyResult] = None


@strawberry.type
class MutationStatus:
    ok: bool
    id: Optional[str] = None
    message: Optional[str] = None


@strawberry.type
class SkillType:
    id: str
    name: str
    description: Optional[str] = None
    active: Optional[bool] = None
    use_count: Optional[int] = None


# ── Context ───────────────────────────────────────────────────────

@strawberry.type
class AerynContext:
    """Shared context for all resolvers."""

    def __init__(self):
        self.safety = get_safety_engine()
        self.vault = AerynVault()
        self.social = SocialMemory()
        self.db = get_shared_db()
        self.search = get_search_engine()
        self.start_time = time.time()


def get_context() -> AerynContext:
    return AerynContext()


# ── Queries ───────────────────────────────────────────────────────

@strawberry.type
class Query:

    @strawberry.field
    def health(self) -> HealthStatus:
        return HealthStatus(
            status="healthy",
            version="40.30",
            uptime_seconds=round(time.time() - get_context().start_time, 1),
            timestamp=time.time(),
        )

    # ── Vault ─────────────────────────────────────────────────────

    @strawberry.field
    def vault_summary(self) -> VaultSummary:
        ctx = get_context()
        counts = ctx.vault.count_entries()
        layers = [VaultLayerCount(layer=k, count=v) for k, v in counts.items()]
        return VaultSummary(total=sum(counts.values()), layers=layers)

    @strawberry.field
    def vault_entries(
        self,
        layer: Optional[str] = None,
        limit: int = 50,
    ) -> List[VaultEntryType]:
        ctx = get_context()
        entries = []
        layers = [layer] if layer else ["Raw", "Wiki", "Projects", "System", "Daily", "Skills"]
        for lyr in layers:
            dirpath = os.path.join(ctx.vault.BASE, lyr)
            if not os.path.isdir(dirpath):
                continue
            for fname in sorted(os.listdir(dirpath)):
                if not fname.endswith(".md"):
                    continue
                fpath = os.path.join(dirpath, fname)
                try:
                    with open(fpath, encoding="utf-8") as f:
                        content = f.read()
                except OSError:
                    continue
                # Parse frontmatter
                title = fname.replace(".md", "").replace("_", " ")
                body = content
                author = "aeryn"
                created = None
                if content.startswith("---"):
                    end = content.find("---", 3)
                    if end > 0:
                        fm = content[3:end]
                        body = content[end + 3:].strip()
                        for line in fm.split("\n"):
                            if line.startswith("title:"):
                                title = line[6:].strip()
                            elif line.startswith("author:"):
                                author = line[7:].strip()
                            elif line.startswith("created:"):
                                created = line[8:].strip()
                entries.append(VaultEntryType(
                    layer=lyr, title=title, body=body[:2000],
                    author=author, created=created, path=fpath,
                ))
                if len(entries) >= limit:
                    break
            if len(entries) >= limit:
                break
        return entries

    @strawberry.field
    def vault_search(self, query: str, limit: int = 10) -> SearchResults:
        ctx = get_context()
        raw = ctx.vault.search(query, limit=limit)
        results = [
            SearchResult(path=r.get("path", ""), layer=r.get("layer"), preview=r.get("preview"))
            for r in raw
        ]
        return SearchResults(query=query, results=results, count=len(results))

    # ── Social ────────────────────────────────────────────────────

    @strawberry.field
    def people(self) -> List[Person]:
        ctx = get_context()
        ctx.social._reload_if_changed()
        result = []
        for key, p in ctx.social._data.get("people", {}).items():
            facts = [
                PersonFact(
                    text=f.get("text", f) if isinstance(f, dict) else str(f),
                    author=f.get("author") if isinstance(f, dict) else None,
                    hash=f.get("hash") if isinstance(f, dict) else None,
                )
                for f in p.get("fakta", [])
            ]
            result.append(Person(
                key=key,
                name=p.get("name", key),
                relation=p.get("relasi"),
                facts=facts,
                last_seen=p.get("last_seen"),
            ))
        return result

    @strawberry.field
    def person(self, key: str) -> Optional[Person]:
        ctx = get_context()
        p = ctx.social.know_person(key)
        if not p:
            return None
        facts = [
            PersonFact(
                text=f.get("text", f) if isinstance(f, dict) else str(f),
                author=f.get("author") if isinstance(f, dict) else None,
                hash=f.get("hash") if isinstance(f, dict) else None,
            )
            for f in p.get("fakta", [])
        ]
        return Person(
            key=key,
            name=p.get("name", key),
            relation=p.get("relasi"),
            facts=facts,
            last_seen=p.get("last_seen"),
        )

    @strawberry.field
    def channels(self) -> List[Channel]:
        ctx = get_context()
        ctx.social._reload_if_changed()
        return [
            Channel(
                key=k,
                name=c.get("name", k),
                role=c.get("peran"),
                last_topic=c.get("topik_terakhir"),
            )
            for k, c in ctx.social._data.get("channels", {}).items()
        ]

    # ── Tasks ─────────────────────────────────────────────────────

    @strawberry.field
    def tasks(self, status_filter: Optional[str] = None) -> List[TaskType]:
        ctx = get_context()
        if status_filter == "pending":
            raw = ctx.db.get_pending_tasks()
        else:
            raw = ctx.db.get_all_task_ids()
        return [
            TaskType(
                id=t["id"],
                title=t.get("title", ""),
                description=t.get("description"),
                status=t.get("status"),
                priority=t.get("priority"),
                progress=t.get("progress"),
            )
            for t in raw
        ]

    @strawberry.field
    def task(self, task_id: str) -> Optional[TaskType]:
        ctx = get_context()
        t = ctx.db.get_task_by_id(task_id)
        if not t:
            return None
        return TaskType(
            id=t["id"],
            title=t.get("title", ""),
            description=t.get("description"),
            status=t.get("status"),
            priority=t.get("priority"),
            progress=t.get("progress"),
            created_at=t.get("created_at"),
            updated_at=t.get("updated_at"),
            completed_at=t.get("completed_at"),
        )

    # ── Reminders ─────────────────────────────────────────────────

    @strawberry.field
    def reminders(self, due_only: bool = False) -> List[ReminderType]:
        ctx = get_context()
        if due_only:
            raw = ctx.db.get_due_reminders()
        else:
            raw = ctx.db.get_all_reminders()
        return [
            ReminderType(
                id=r["id"],
                text=r.get("text", ""),
                due_at=r.get("due_at"),
                status=r.get("status"),
                source=r.get("source"),
                target=r.get("target"),
            )
            for r in raw
        ]

    # ── Search ────────────────────────────────────────────────────

    @strawberry.field
    def search(self, query: str, limit: int = 10) -> SearchResults:
        ctx = get_context()
        try:
            raw = ctx.search.search(query, limit=limit)
        except Exception:
            raw = []
        results = [
            SearchResult(
                path=r.get("path", r.get("source", "")),
                layer=r.get("layer"),
                preview=r.get("preview", r.get("content", ""))[:300] if r.get("preview") or r.get("content") else None,
            )
            for r in raw
        ]
        return SearchResults(query=query, results=results, count=len(results))

    # ── Stats ─────────────────────────────────────────────────────

    @strawberry.field
    def stats(self) -> StatsType:
        ctx = get_context()
        db_stats = ctx.db.get_stats()
        vault_counts = ctx.vault.count_entries()
        ctx.social._reload_if_changed()
        return StatsType(
            reminders_total=db_stats.get("reminders", {}).get("total", 0),
            reminders_pending=db_stats.get("reminders", {}).get("pending", 0),
            tasks_total=db_stats.get("tasks", {}).get("total", 0),
            tasks_pending=db_stats.get("tasks", {}).get("pending", 0),
            tasks_completed=db_stats.get("tasks", {}).get("completed", 0),
            notifications_total=db_stats.get("notifications", {}).get("total", 0),
            vault_total=sum(vault_counts.values()),
            social_people=len(ctx.social._data.get("people", {})),
        )


# ── Mutations ─────────────────────────────────────────────────────

@strawberry.type
class Mutation:

    @strawberry.mutation
    def run_goal(self, goal: str, session_id: Optional[str] = None) -> RunGoalResult:
        ctx = get_context()
        safety = ctx.safety.check_input(goal)
        sid = session_id or str(uuid.uuid4())[:12]

        if not safety.safe:
            return RunGoalResult(
                status="blocked",
                session_id=sid,
                response="",
                safety=SafetyResult(
                    safe=False,
                    risk=safety.risk,
                    reason=safety.reason,
                    fallback=safety.fallback,
                ),
            )

        response = sanitize_output(f"Processing: {goal[:500]}")
        return RunGoalResult(
            status="ok",
            session_id=sid,
            response=response,
            safety=SafetyResult(safe=True, risk=safety.risk),
        )

    @strawberry.mutation
    def remember(
        self,
        person_key: str,
        fact: str,
        name: Optional[str] = None,
    ) -> MutationStatus:
        ctx = get_context()
        ok = ctx.social.add_fact(person_key, fact, nama=name or "")
        return MutationStatus(ok=ok, message="Fact stored" if ok else "Duplicate or invalid")

    @strawberry.mutation
    def add_task(
        self,
        title: str,
        description: Optional[str] = None,
        priority: int = 5,
    ) -> MutationStatus:
        ctx = get_context()
        tid = ctx.db.add_task(title, description or "", priority)
        return MutationStatus(ok=True, id=tid, message="Task created")

    @strawberry.mutation
    def update_task(
        self,
        task_id: str,
        status: Optional[str] = None,
        progress: Optional[float] = None,
        result: Optional[str] = None,
    ) -> MutationStatus:
        ctx = get_context()
        ctx.db.update_task(task_id, status=status, progress=progress, result=result)
        return MutationStatus(ok=True, id=task_id, message="Task updated")

    @strawberry.mutation
    def add_reminder(
        self,
        text: str,
        due_at: str,
        source: Optional[str] = "graphql",
        target: Optional[str] = "all",
    ) -> MutationStatus:
        ctx = get_context()
        rid = ctx.db.add_reminder(text, due_at, source or "graphql", target or "all")
        return MutationStatus(ok=True, id=rid, message="Reminder added")

    @strawberry.mutation
    def write_vault_entry(
        self,
        layer: str,
        title: str,
        body: str,
        tags: Optional[str] = None,
    ) -> MutationStatus:
        ctx = get_context()
        tag_list = [t.strip() for t in tags.split(",")] if tags else []
        entry = VaultEntry(layer=layer, title=title, body=body, tags=tag_list)
        path = ctx.vault.write(entry)
        return MutationStatus(ok=True, id=entry.hash, message=f"Written to {path}")

    @strawberry.mutation
    def append_daily(self, section: str, content: str) -> MutationStatus:
        ctx = get_context()
        ctx.vault.append_daily(section, content)
        return MutationStatus(ok=True, message=f"Appended to {section}")

    @strawberry.mutation
    def set_preference(
        self,
        person_key: str,
        pref_key: str,
        value: str,
    ) -> MutationStatus:
        ctx = get_context()
        ok = ctx.social.set_preference(person_key, pref_key, value)
        return MutationStatus(ok=ok, message="Preference set" if ok else "Invalid person")

    @strawberry.mutation
    def set_relation(
        self,
        person_key: str,
        relation: str,
        name: Optional[str] = None,
    ) -> MutationStatus:
        ctx = get_context()
        ok = ctx.social.set_relation(person_key, relation, nama=name or "")
        return MutationStatus(ok=ok, message="Relation set" if ok else "Invalid person")


# ── Schema ────────────────────────────────────────────────────────

schema = strawberry.Schema(query=Query, mutation=Mutation)


# ── Standalone Runner ─────────────────────────────────────────────

def create_app():
    """Create a FastAPI app with GraphQL mounted at /graphql."""
    from fastapi import FastAPI
    from strawberry.fastapi import GraphQLRouter

    app = FastAPI(title="Aeryn GraphQL API", version="40.30")
    graphql_app = GraphQLRouter(schema)
    app.include_router(graphql_app, prefix="/graphql")

    @app.get("/health")
    async def health():
        return {"status": "healthy", "version": "40.30", "graphql": "/graphql"}

    return app


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Aeryn GraphQL API")
    parser.add_argument("--port", type=int, default=3012, help="Port to listen on")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind")
    parser.add_argument("--mount", action="store_true", help="Print FastAPI mount snippet")
    args = parser.parse_args()

    if args.mount:
        print("""
# Mount into existing FastAPI app:
from strawberry.fastapi import GraphQLRouter
from aeryn_core.platform.graphql_api import schema

graphql_app = GraphQLRouter(schema, path="/graphql")
app.include_router(graphql_app, prefix="/graphql")
""")
        sys.exit(0)

    ensure_dirs()
    import uvicorn

    app = create_app()
    print(f"🚀 Aeryn GraphQL API v40.30 starting on http://{args.host}:{args.port}/graphql")
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
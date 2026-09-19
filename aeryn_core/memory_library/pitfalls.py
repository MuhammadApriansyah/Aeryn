#!/usr/bin/env python3
"""
pitfalls.py — Self-healing pitfall library.

Every hard-won lesson about THIS environment gets recorded here so the
same mistake is never re-diagnosed twice. Before debugging anything,
search this first:

    python3 pitfalls.py search "gateway restart blocked"
    python3 pitfalls.py add <signature> "<symptom>" "<root cause>" "<fix>"
    python3 pitfalls.py list [--limit N]

The agent's EVOLVE step writes here immediately after solving a non-trivial
error. Entries are also linked into the graph via graph_rag.py.
"""
import sqlite3
import os
import sys
import argparse

DB = os.environ.get(
    "MEMORY_GRAPH_DB",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "library", "memory_graph.db"))


def conn():
    c = sqlite3.connect(DB, timeout=10)
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA busy_timeout=5000")
    c.execute("""CREATE TABLE IF NOT EXISTS pitfalls
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         signature TEXT NOT NULL,
         symptom TEXT NOT NULL,
         root_cause TEXT NOT NULL,
         fix TEXT NOT NULL,
         source TEXT,
         created_at TEXT DEFAULT (datetime('now')),
         UNIQUE(signature))""")
    return c


def add(signature, symptom, root_cause, fix, source="session"):
    c = conn()
    try:
        c.execute("INSERT INTO pitfalls (signature, symptom, root_cause, fix, source) VALUES (?,?,?,?,?)",
                  (signature.lower()[:80], symptom[:300], root_cause[:300], fix[:500], source))
        c.commit()
        pid = c.execute("SELECT last_insert_rowid()").fetchone()[0]
        print(f"[pitfall #{pid}] saved: {signature}")
    except sqlite3.IntegrityError:
        print(f"[pitfall] duplicate signature '{signature}' — updating fix/root-cause instead")
        c.execute("UPDATE pitfalls SET symptom=?, root_cause=?, fix=? WHERE signature=?",
                  (symptom[:300], root_cause[:300], fix[:500], signature.lower()[:80]))
        c.commit()
        print(f"[pitfall] updated")
    finally:
        c.close()


def search(query, limit=5):
    terms = [t for t in query.lower().split() if len(t) > 2]
    c = conn()
    rows = c.execute("SELECT id, signature, symptom, root_cause, fix FROM pitfalls").fetchall()
    c.close()
    scored = []
    for r in rows:
        blob = f"{r[1]} {r[2]} {r[3]} {r[4]}".lower()
        score = sum(1 for t in terms if t in blob)
        if score:
            scored.append((score, r))
    scored.sort(key=lambda x: -x[0])
    if not scored:
        print(f"[search] no pitfalls match '{query}' — treat as unknown problem")
        return
    for score, r in scored[:limit]:
        print(f"\n#{r[0]} [{r[1]}] (match {score})")
        print(f"  symptom   : {r[2]}")
        print(f"  root cause: {r[3]}")
        print(f"  fix       : {r[4]}")


def list_all(limit=20):
    c = conn()
    rows = c.execute("SELECT id, signature, created_at FROM pitfalls ORDER BY id DESC LIMIT ?",
                     (limit,)).fetchall()
    c.close()
    print(f"[list] {len(rows)} pitfalls:")
    for r in rows:
        print(f"  #{r[0]} [{r[1]}] {r[2]}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Pitfall library (self-healing memory)")
    sub = p.add_subparsers(dest="cmd", required=True)
    pa = sub.add_parser("add")
    pa.add_argument("signature"); pa.add_argument("symptom")
    pa.add_argument("root_cause"); pa.add_argument("fix")
    pa.add_argument("--source", default="session")
    ps = sub.add_parser("search"); ps.add_argument("query"); ps.add_argument("--limit", type=int, default=5)
    pl = sub.add_parser("list"); pl.add_argument("--limit", type=int, default=20)
    args = p.parse_args()

    if args.cmd == "add":
        add(args.signature, args.symptom, args.root_cause, args.fix, args.source)
    elif args.cmd == "search":
        search(args.query, args.limit)
    elif args.cmd == "list":
        list_all(args.limit)

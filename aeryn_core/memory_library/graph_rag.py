#!/usr/bin/env python3
"""
graph_rag.py — Unified Graph RAG nerve center.

Nodes = entities (projects, services, tools, people, prefs).
Edges = relations between them.

Subcommands:
  init                          Create tables (WAL mode for concurrent writers)
  add_node <id> <type> <summary> [path]
  add_edge <source> <target> <relation> [weight]
  traverse <entity> [depth]     BFS around entity, condensed context output
  status                        Node/edge counts + mount health
"""
import sqlite3
import os
import sys
import argparse

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get(
    "MEMORY_GRAPH_DB", os.path.join(_SCRIPT_DIR, "library", "memory_graph.db"))
LOCAL_FALLBACK_DB = os.environ.get(
    "MEMORY_GRAPH_DB_LOCAL", os.path.expanduser("~/.hermes/memory_graph_local.db"))
_mount_alerted = False


def get_active_db():
    """Survival mode: fall back to local DB if Android mount is gone."""
    global _mount_alerted
    lib_dir = os.path.dirname(DB_PATH)
    if os.path.isdir(lib_dir):
        return DB_PATH
    if not _mount_alerted:
        print(f"[ALERT] Android mount MISSING — using local fallback {LOCAL_FALLBACK_DB}",
              file=sys.stderr)
        _mount_alerted = True
    return LOCAL_FALLBACK_DB


def connect():
    db = get_active_db()
    os.makedirs(os.path.dirname(db), exist_ok=True)
    conn = sqlite3.connect(db, timeout=10)
    # WAL = concurrent sub-agent writes don't corrupt / block each other
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("""CREATE TABLE IF NOT EXISTS nodes
                 (id TEXT PRIMARY KEY, type TEXT, summary TEXT, path TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS edges
                 (source TEXT, target TEXT, relation TEXT, weight INTEGER,
                  PRIMARY KEY (source, target, relation))""")
    return conn


def resolve(entity):
    """Exact match first, then substring — returns list of node ids."""
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT id FROM nodes WHERE id = ?", (entity,))
    exact = [r[0] for r in c.fetchall()]
    if exact:
        conn.close()
        return exact
    c.execute("SELECT id FROM nodes WHERE id LIKE ? OR type LIKE ? OR summary LIKE ?",
              (f"%{entity}%", f"%{entity}%", f"%{entity}%"))
    ids = [r[0] for r in c.fetchall()]
    conn.close()
    return ids


def cmd_traverse(entity, depth=2):
    seeds = resolve(entity)
    if not seeds:
        print(f"[traverse] no node matches '{entity}'")
        return
    conn = connect()
    c = conn.cursor()
    visited = set(seeds)
    queue = [(s, 0) for s in seeds]
    lines = []
    while queue:
        current, d = queue.pop(0)
        c.execute("SELECT id, type, summary, path FROM nodes WHERE id = ?", (current,))
        row = c.fetchone()
        if row:
            prefix = "  " * d
            path_hint = f" [lib:{row[3]}]" if row[3] else ""
            lines.append(f"{prefix}{row[0]} ({row[1]}){path_hint}: {row[2]}")
        if d >= depth:
            continue
        # both directions
        c.execute("SELECT target, relation FROM edges WHERE source = ?", (current,))
        for target, rel in c.fetchall():
            lines.append(f"{'  ' * (d + 1)}--{rel}--> {target}")
            if target not in visited:
                visited.add(target)
                queue.append((target, d + 1))
        c.execute("SELECT source, relation FROM edges WHERE target = ?", (current,))
        for source, rel in c.fetchall():
            lines.append(f"{'  ' * (d + 1)}<--{rel}-- {source}")
            if source not in visited:
                visited.add(source)
                queue.append((source, d + 1))
    conn.close()
    print("\n".join(lines))


def cmd_add_node(nid, ntype, summary, path=None):
    conn = connect()
    conn.execute("INSERT OR REPLACE INTO nodes VALUES (?, ?, ?, ?)",
                 (nid, ntype, summary, path))
    conn.commit()
    conn.close()
    print(f"[node] {nid} ({ntype}) saved")


def cmd_add_edge(src, dst, rel, weight=1):
    # write-through guard: refuse dangling edges to unknown nodes
    known_src, known_dst = resolve(src), resolve(dst)
    if not known_src:
        print(f"[edge] WARN: source '{src}' unknown — adding placeholder node", file=sys.stderr)
        cmd_add_node(src, "unknown", "(auto-created by edge write)", None)
    if not known_dst:
        print(f"[edge] WARN: target '{dst}' unknown — adding placeholder node", file=sys.stderr)
        cmd_add_node(dst, "unknown", "(auto-created by edge write)", None)
    conn = connect()
    conn.execute("INSERT OR REPLACE INTO edges VALUES (?, ?, ?, ?)",
                 (src, dst, rel, weight))
    conn.commit()
    conn.close()
    print(f"[edge] {src} --{rel}--> {dst} (w={weight})")


def cmd_status():
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM nodes"); n = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM edges"); e = c.fetchone()[0]
    c.execute("SELECT type, COUNT(*) FROM nodes GROUP BY type ORDER BY 2 DESC")
    breakdown = c.fetchall()
    conn.close()
    db = get_active_db()
    mode = "ANDROID MOUNT" if db == DB_PATH else "** LOCAL FALLBACK (mount missing!) **"
    print(f"db: {db}")
    print(f"mode: {mode}")
    print(f"nodes: {n} | edges: {e}")
    for t, cnt in breakdown:
        print(f"  {t}: {cnt}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Unified Graph RAG")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init")

    pn = sub.add_parser("add_node")
    pn.add_argument("id"); pn.add_argument("type"); pn.add_argument("summary")
    pn.add_argument("path", nargs="?", default=None)

    pe = sub.add_parser("add_edge")
    pe.add_argument("source"); pe.add_argument("target"); pe.add_argument("relation")
    pe.add_argument("--weight", type=int, default=1)

    pt = sub.add_parser("traverse")
    pt.add_argument("entity")
    pt.add_argument("--depth", type=int, default=2)

    sub.add_parser("status")
    args = p.parse_args()

    if args.cmd == "init":
        connect(); print("graph initialized")
    elif args.cmd == "add_node":
        cmd_add_node(args.id, args.type, args.summary, args.path)
    elif args.cmd == "add_edge":
        cmd_add_edge(args.source, args.target, args.relation, args.weight)
    elif args.cmd == "traverse":
        cmd_traverse(args.entity, args.depth)
    elif args.cmd == "status":
        cmd_status()

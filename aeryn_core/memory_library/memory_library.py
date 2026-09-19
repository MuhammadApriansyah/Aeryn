#!/usr/bin/env python3
"""
memory_library.py — Library memory store (cold tier, RAG-style retrieval).

NOT vector-only: ranks by tag-match + keyword + signal + recency, then
returns CONDENSED entries (not raw dumps). Designed for sub-agent retrieval.

Subcommands:
  build    Rebuild INDEX.json from all topic files
  search   Query the library, return top-N condensed entries
  add      Add a new entry (auto-classify by topic)
  curate   Report signal distribution + stale entries (for curation sub-agent)

Library lives at /mnt/android/Ubuntu/hermes-memory-library/
Internal memory (MEMORY.md) is the HOT tier — always in context.
"""
import argparse, json, os, sys, re, glob
from datetime import datetime, timezone

LIB = os.environ.get(
    "MEMORY_LIBRARY",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "library"))
INDEX = os.path.join(LIB, "INDEX.json")

TOPIC_KEYWORDS = {
    "webnovel": ["webnovel", "epub", "parser", "calibre", "navbar", "fastify",
                  "playwright", "chapter", "cmdk", "sonner", "framer", "spine",
                  "vite", "sqlite", "web novel"],
    "discord": ["discord", "alpha", "guild", "bot", "koya", "owo", "jockie",
                 "flavibot", "haruka", "channel", "server", "role gate"],
    "aeryn": ["aeryn", "arisylla", "cognitive", "sde", "tensor", "rust vault",
               "division", "planner", "sub-agent", "persona"],
    "hermes-infra": ["gateway", "gwctl", "backup", "memory", "profile", "multiplex",
                      "cron", "proot", "pm2", "symlink", "hermes", "android mount"],
    "user-prefs": ["communication", "concise", "indonesian", "frustrated", "proactive",
                    "credential", "preference", "style", "sen"],
    "spark": ["gemini", "spark", "mcp", "oauth", "google drive"],
}

def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")

def classify(text):
    text_l = text.lower()
    scores = {t: sum(text_l.count(k) for k in kws) for t, kws in TOPIC_KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "misc"

def parse_entry(path):
    with open(path) as f:
        raw = f.read()
    fm = {}
    m = re.match(r"^---\n(.*?)\n---\n", raw, re.S)
    body = raw
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                fm[k.strip()] = v.strip()
        body = raw[m.end():]
    return fm, body.strip()

def index_build():
    entries = []
    for path in glob.glob(os.path.join(LIB, "**", "*.md"), recursive=True):
        if os.path.basename(path) == "INDEX.json":
            continue
        fm, body = parse_entry(path)
        rel = os.path.relpath(path, LIB)
        entries.append({
            "id": fm.get("id", os.path.splitext(os.path.basename(path))[0]),
            "topic": fm.get("topic", classify(body)),
            "tags": fm.get("tags", "").strip("[]").split(",") if fm.get("tags") else [],
            "signal": fm.get("signal", "med"),
            "summary": fm.get("summary", body[:120].replace("\n", " ")),
            "path": rel,
            "updated": fm.get("updated", now_iso()),
        })
    with open(INDEX, "w") as f:
        json.dump({"entries": entries, "built": now_iso()}, f, indent=2)
    print(f"[build] indexed {len(entries)} entries → {INDEX}")

def search(query, top=5, topic=None):
    if not os.path.exists(INDEX):
        index_build()
    with open(INDEX) as f:
        data = json.load(f)
    # semantic expansion (L2): original terms + synonyms + LLM suggestions
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from query_expander import expand
        q_terms = expand(query)
    except Exception:
        q_terms = re.findall(r"\w+", query.lower())
    scored = []
    # hybrid: also compute cosine similarity against cached embeddings (L2+)
    vec_scores = {}
    try:
        from embedder import embed, cosine, _hash, _conn, _entry_text
        qvec, qmethod = embed(query)
        for e in data["entries"]:
            if topic and e["topic"] != topic:
                continue
            path = os.path.join(LIB, e["path"])
            if not os.path.exists(path):
                continue
            with open(path) as fh:
                raw = fh.read()
            text = _entry_text(raw)
            row = _conn().execute(
                "SELECT method, vector FROM embeddings WHERE text_hash=?",
                (_hash(text),)).fetchone()
            if row and row[0] == qmethod:
                vec_scores[e["id"]] = cosine(qvec, json.loads(row[1].decode()))
    except Exception as ex:
        print(f"[search] vector lane skipped: {ex}")

    for e in data["entries"]:
        if topic and e["topic"] != topic:
            continue
        tags = [t.lower() for t in e["tags"]]
        score = 0
        for t in q_terms:
            if t in tags:
                score += 3
            if t in e["summary"].lower():
                score += 2
            if t in e["id"].lower():
                score += 1
        # signal bonus + usage bonus (L3: frequently-retrieved entries rank higher)
        sig_bonus = {"high": 2, "med": 1, "low": 0}.get(e["signal"], 1)
        use_bonus = min(e.get("access_count", 0), 5) * 0.4
        score += sig_bonus + use_bonus
        # V34 — temporal validity: entry yang sudah digantikan di-deprioritaskan
        if e.get("superseded_by"):
            score *= 0.25
            stale = True
        else:
            stale = False
        # hybrid fusion: when a vector score exists it carries the semantic
        # signal; keywords still contribute but can't override a clear
        # embedding gap (0.58 vs 0.52 = ~1 point spread after scaling)
        vscore = vec_scores.get(e["id"])
        if vscore is not None:
            score = score * 0.35 + vscore * 14 * 0.65
        if score > 0.5:
            scored.append((score, e))
    scored.sort(key=lambda x: x[0], reverse=True)
    out = []
    for score, e in scored[:top]:
        path = os.path.join(LIB, e["path"])
        body = ""
        if os.path.exists(path):
            fm, body = parse_entry(path)
            body = body[:600]  # condense
            # V34 — tanda eksplisit kalau entry sudah digantikan
            if fm.get("superseded_by"):
                body = (f"⚠️ SUDAH DIGANTIKAN oleh '{fm['superseded_by']}'"
                        f"{(' — ' + fm['superseded_reason']) if fm.get('superseded_reason') else ''}. "
                        f"Ini konteks sejarah:\n{body}")
        _track_access(e)
        out.append(f"### {e['id']} [{e['topic']}/{e['signal']}] (score {score:.1f})\n{body}\n")
    print(f"[search] {len(out)} results for '{query}' "
          f"(expanded to {len(q_terms)} terms)" + (f" topic={topic}" if topic else ""))
    print("\n---\n".join(out) if out else "[search] no matches")


def _track_access(entry):
    """L3 usage tracking: increment access_count in INDEX (best-effort)."""
    try:
        with open(INDEX) as f:
            data = json.load(f)
        for e in data["entries"]:
            if e["id"] == entry["id"]:
                e["access_count"] = e.get("access_count", 0) + 1
                break
        with open(INDEX, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

def add(topic, tags, signal, summary, body, entry_id=None):
    topic_dir = os.path.join(LIB, topic)
    os.makedirs(topic_dir, exist_ok=True)
    if not entry_id:
        existing = glob.glob(os.path.join(topic_dir, "*.md"))
        entry_id = f"{topic}-{len(existing)+1:03d}"
    path = os.path.join(topic_dir, f"{entry_id}.md")
    fm = (f"---\nid: {entry_id}\ntopic: {topic}\ntags: [{tags}]\n"
          f"signal: {signal}\ncreated: {now_iso()}\nupdated: {now_iso()}\n"
          f"summary: {summary}\n---\n")
    with open(path, "w") as f:
        f.write(fm + body + "\n")
    index_build()
    print(f"[add] {entry_id} → {path}")


def supersede(old_id, new_id, reason=""):
    """V34 — tandai entry lama DIGANTIKAN oleh yang baru (temporal validity).

    Frontmatter lama dapat `superseded_by: <new_id>` + signal turun ke low,
    sehingga search tetap menemukannya (konteks sejarah) tapi jelas tertanda
    usang dan tidak lagi mendominasi ranking.
    """
    if not os.path.exists(INDEX):
        index_build()
    with open(INDEX) as f:
        data = json.load(f)
    targets = {}
    for e in data["entries"]:
        if e["id"] == old_id or e["id"] == new_id:
            targets[e["id"]] = e
    for wanted in (old_id, new_id):
        if wanted not in targets:
            print(f"[supersede] entry '{wanted}' tidak ditemukan")
            return 1
    old_path = os.path.join(LIB, targets[old_id]["path"])
    raw = open(old_path).read()
    m = re.match(r"^---\n(.*?)\n---\n", raw, re.S)
    body_only = raw[m.end():] if m else raw
    fm, _ = parse_entry(old_path)
    fm["superseded_by"] = new_id
    fm["superseded_at"] = now_iso()
    if reason:
        fm["superseded_reason"] = reason[:120]
    fm["signal"] = "low"
    lines = ["---"] + [f"{k}: {v}" for k, v in fm.items()] + ["---", ""]
    with open(old_path, "w") as f:
        f.write("\n".join(lines) + "\n" + body_only)
    index_build()
    print(f"[supersede] {old_id} → digantikan oleh {new_id}"
          f"{f' ({reason})' if reason else ''}")
    return 0

def curate():
    if not os.path.exists(INDEX):
        index_build()
    with open(INDEX) as f:
        data = json.load(f)
    by_topic = {}
    for e in data["entries"]:
        by_topic.setdefault(e["topic"], {"high":0,"med":0,"low":0})
        by_topic[e["topic"]][e["signal"]] = by_topic[e["topic"]].get(e["signal"],0)+1
    print("[curate] signal distribution by topic:")
    for t, s in by_topic.items():
        print(f"  {t}: high={s.get('high',0)} med={s.get('med',0)} low={s.get('low',0)}")
    print(f"[curate] total: {len(data['entries'])} entries")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("build")
    ps = sub.add_parser("search"); ps.add_argument("query"); ps.add_argument("--top", type=int, default=5); ps.add_argument("--topic")
    pa = sub.add_parser("add"); pa.add_argument("topic"); pa.add_argument("tags"); pa.add_argument("signal"); pa.add_argument("summary"); pa.add_argument("body"); pa.add_argument("--id")
    psup = sub.add_parser("supersede"); psup.add_argument("old_id"); psup.add_argument("new_id"); psup.add_argument("--reason", default="")
    sub.add_parser("curate")
    args = p.parse_args()
    if args.cmd == "build": index_build()
    elif args.cmd == "search": search(args.query, args.top, args.topic)
    elif args.cmd == "add": add(args.topic, args.tags, args.signal, args.summary, args.body, args.id)
    elif args.cmd == "supersede": sys.exit(supersede(args.old_id, args.new_id, args.reason))
    elif args.cmd == "curate": curate()
    else: p.print_help()

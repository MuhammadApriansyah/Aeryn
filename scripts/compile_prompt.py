#!/usr/bin/env python3
"""compile_prompt.py — Compile system prompt diperkaya konteks via aeryn-core.

Output JSON ke stdout:
{ "compiled_prompt": "...", "blackboard": {...}, "gate_mode": N }
"""
import argparse
import json
import sys

sys.path.insert(0, "/home/sen/aeryn-core-agent")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", required=True)
    ap.add_argument("--base-prompt", required=True)
    ap.add_argument("--user-prompt", required=True)
    ap.add_argument("--history-file", default=None, help="JSON array of 'role: text' strings")
    ap.add_argument("--tasks-file", default=None, help="JSON array of task strings")
    args = ap.parse_args()

    history = []
    if args.history_file:
        with open(args.history_file) as f:
            history = json.load(f)

    tasks = []
    if args.tasks_file:
        with open(args.tasks_file) as f:
            tasks = json.load(f)

    # Import berat setelah argumen valid (fail fast)
    from aeryn_core.orchestrator import UnifiedCognitiveOrchestrator

    brain = UnifiedCognitiveOrchestrator(dimension=384)
    compiled = brain.compile_stateful_system_prompt(
        session_id=args.session,
        base_character_prompt=args.base_prompt,
        user_prompt=args.user_prompt,
        mock_history_logs=history,
        open_tasks=tasks,
    )

    try:
        blackboard = json.loads(brain.cached_shared_blackboard)
    except Exception:
        blackboard = {}

    print(json.dumps({
        "compiled_prompt": compiled,
        "blackboard": blackboard,
        "gate_mode": brain.cached_active_gate_mode,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()

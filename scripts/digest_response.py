#!/usr/bin/env python3
"""digest_response.py — Analisis respons LLM via aeryn-core.

Output JSON ke stdout: status, compliance, ledger audit, memory telemetry.
"""
import argparse
import json
import sys

sys.path.insert(0, "/home/sen/aeryn-core-agent")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", required=True)
    ap.add_argument("--user-prompt", required=True)
    ap.add_argument("--response-file", default=None, help="File teks respons; default stdin")
    args = ap.parse_args()

    if args.response_file:
        with open(args.response_file) as f:
            response = f.read()
    else:
        response = sys.stdin.read()

    from aeryn_core.platform.orchestrator import UnifiedCognitiveOrchestrator

    brain = UnifiedCognitiveOrchestrator(dimension=384)
    result = brain.digest_external_llm_response(
        session_id=args.session,
        user_prompt=args.user_prompt,
        raw_llm_output_text=response,
    )

    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()

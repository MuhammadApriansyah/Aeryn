#!/usr/bin/env python3
"""V40.42 — CLI Interface: Terminal commands for Aeryn."""

import os, sys, json, argparse
from typing import Dict, List

def main():
    parser = argparse.ArgumentParser(description="Aeryn CLI")
    subparsers = parser.add_subparsers(dest="command")
    
    # Run command
    run_parser = subparsers.add_parser("run", help="Run a goal")
    run_parser.add_argument("goal", help="Goal to execute")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search memories")
    search_parser.add_argument("query", help="Search query")
    
    # Task command
    task_parser = subparsers.add_parser("task", help="Manage tasks")
    task_parser.add_argument("action", choices=["create", "list", "complete"])
    task_parser.add_argument("--title", help="Task title")
    
    # Health command
    subparsers.add_parser("health", help="Check health")
    
    args = parser.parse_args()
    
    import urllib.request
    
    if args.command == "run":
        req = urllib.request.Request(
            "http://127.0.0.1:3010/run",
            data=json.dumps({"goal": args.goal}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
            print(result.get("response", "No response"))
    
    elif args.command == "search":
        req = urllib.request.Request(
            f"http://127.0.0.1:3010/search?q={args.query}",
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode())
            for r in result.get("results", []):
                print(f"- {r.get('title', 'Untitled')}")
    
    elif args.command == "task":
        if args.action == "create" and args.title:
            req = urllib.request.Request(
                f"http://127.0.0.1:3010/shared/tasks/add?title={args.title}",
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode())
                print(f"Task created: {result.get('id', '?')}")
        elif args.action == "list":
            req = urllib.request.Request(
                "http://127.0.0.1:3010/shared/tasks",
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode())
                for t in result.get("tasks", []):
                    print(f"[{t.get('status', '?')}] {t.get('title', 'Untitled')}")
    
    elif args.command == "health":
        req = urllib.request.Request("http://127.0.0.1:3010/health", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            result = json.loads(resp.read().decode())
            print(f"Status: {result.get('status', 'unknown')}")
            print(f"Version: {result.get('version', '?')}")
            print(f"Memory: {result.get('memory_mb', '?')}MB")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

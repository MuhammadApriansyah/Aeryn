#!/usr/bin/env python3
"""V39.71 — Structured Output: Generate docs, sheets, JSON, and formatted responses.

Output formats:
- Markdown docs (reports, guides, documentation)
- JSON (structured data)
- CSV (spreadsheets)
- Plain text
"""

import os
import sys
import json
import csv
import io
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aeryn_core.memory.vault import AerynVault, VaultEntry, LAYER_WIKI
from aeryn_core.database.shared_db import get_shared_db
from aeryn_core.utils.config import ensure_dirs

class StructuredOutput:
    """Generate structured output in various formats."""
    
    @staticmethod
    def generate_report(title: str, sections: List[Dict[str, str]]) -> str:
        """Generate a markdown report."""
        lines = [f"# {title}", f"\n*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"]
        
        for section in sections:
            heading = section.get("heading", "Section")
            content = section.get("content", "")
            level = section.get("level", 2)
            lines.append(f"\n{'#' * level} {heading}\n")
            lines.append(content)
        
        return "\n".join(lines)
    
    @staticmethod
    def generate_json(data: dict, pretty: bool = True) -> str:
        """Generate formatted JSON."""
        if pretty:
            return json.dumps(data, indent=2, ensure_ascii=False)
        return json.dumps(data, ensure_ascii=False)
    
    @staticmethod
    def generate_csv(headers: List[str], rows: List[List[str]]) -> str:
        """Generate CSV."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        writer.writerows(rows)
        return output.getvalue()
    
    @staticmethod
    def generate_daily_summary() -> str:
        """Generate daily summary report."""
        db = get_shared_db()
        vault = AerynVault()
        log = db.get_or_create_daily_log()
        stats = db.get_stats()
        
        report = StructuredOutput.generate_report(
            f"Daily Summary — {log['date']}",
            [
                {
                    "heading": "System Health",
                    "content": f"- Status: {log.get('system_health', 'unknown')}\n- Interactions today: {log.get('interactions', 0)}",
                    "level": 2
                },
                {
                    "heading": "Tasks",
                    "content": f"- Pending: {stats['tasks']['pending']}\n- Completed: {stats['tasks']['completed']}",
                    "level": 2
                },
                {
                    "heading": "Reminders",
                    "content": f"- Total: {stats['reminders']['total']}\n- Pending: {stats['reminders']['pending']}",
                    "level": 2
                },
                {
                    "heading": "Workflows",
                    "content": f"- Total runs: {stats['workflows']['total_runs']}\n- Successful: {stats['workflows']['successful']}\n- Failed: {stats['workflows']['failed']}",
                    "level": 2
                }
            ]
        )
        
        return report
    
    @staticmethod
    def generate_vault_index() -> str:
        """Generate vault index as markdown."""
        vault = AerynVault()
        counts = vault.count_entries()
        
        sections = []
        for layer, count in counts.items():
            entries = vault.search("", layer=layer, limit=100)
            items = "\n".join([f"- [{e.get('path', '').split('/')[-1]}]({e.get('path', '')})" for e in entries[:20]])
            sections.append({
                "heading": f"{layer} ({count} entries)",
                "content": items if items else "- No entries",
                "level": 3
            })
        
        return StructuredOutput.generate_report("Vault Index", sections)
    
    @staticmethod
    def generate_task_report() -> str:
        """Generate task progress report."""
        db = get_shared_db()
        tasks = db.get_pending_tasks()
        
        headers = ["ID", "Title", "Description", "Priority", "Progress"]
        rows = []
        for t in tasks:
            rows.append([
                t.get("id", ""),
                t.get("title", ""),
                t.get("description", "")[:50],
                str(t.get("priority", "")),
                f"{t.get('progress', 0) * 100:.0f}%"
            ])
        
        csv_data = StructuredOutput.generate_csv(headers, rows)
        
        report = StructuredOutput.generate_report(
            "Task Progress Report",
            [
                {
                    "heading": "Pending Tasks",
                    "content": f"```\n{csv_data}\n```",
                    "level": 2
                }
            ]
        )
        
        return report
    
    @staticmethod
    def generate_reflection_log(reflection: str, interactions: int = 0) -> str:
        """Generate daily reflection log entry."""
        return StructuredOutput.generate_report(
            f"Daily Reflection — {datetime.now().strftime('%Y-%m-%d')}",
            [
                {
                    "heading": "Reflection",
                    "content": reflection,
                    "level": 2
                },
                {
                    "heading": "Statistics",
                    "content": f"- Interactions: {interactions}\n- Generated: {datetime.now().strftime('%H:%M:%S')}",
                    "level": 2
                }
            ]
        )


if __name__ == "__main__":
    print("=== Structured Output Test ===")
    
    # Daily summary
    print("\n1. Daily Summary:")
    print(StructuredOutput.generate_daily_summary())
    
    # Vault index
    print("\n2. Vault Index:")
    print(StructuredOutput.generate_vault_index()[:500])
    
    # Task report
    print("\n3. Task Report:")
    print(StructuredOutput.generate_task_report())
    
    # Reflection log
    print("\n4. Reflection Log:")
    print(StructuredOutput.generate_reflection_log("Today was productive. Built several features.", 15))

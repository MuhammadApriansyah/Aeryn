"""Evaluation Harness — continuous evaluation metrics for Aeryn.

Berdasarkan riset (arXiv 2507.21504, Samira Ghodratnama / Google, MAESTRO):
- Success rate: fraction of episodes fully completed
- Stepwise progress rate: milestones/subgoals achieved (partial credit)
- Tool selection accuracy: correct tool chosen
- Parameter accuracy: correct arguments formatting
- Efficacy: tool call actually improved the answer
- Failure attribution: trace back which agent/step introduced error

Prinsip: evaluasi BUKAN bagian tracing — butuh lapisan evaluasi terpisah.
"""

import os
import json
import sqlite3
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from aeryn_core.utils.config import DATABASE_DIR


@dataclass
class EvalResult:
    """Result of a single evaluation episode."""
    episode_id: str
    task: str
    expected_outcome: str
    success: bool
    progress_rate: float  # 0.0 - 1.0
    tool_selection_accuracy: float  # 0.0 - 1.0
    parameter_accuracy: float  # 0.0 - 1.0
    efficacy: float  # 0.0 - 1.0
    expected_tools: List[str] = field(default_factory=list)
    actual_tools: List[str] = field(default_factory=list)
    milestones: List[str] = field(default_factory=list)
    achieved_milestones: List[str] = field(default_factory=list)
    notes: str = ""
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "task": self.task,
            "expected_outcome": self.expected_outcome,
            "success": self.success,
            "progress_rate": self.progress_rate,
            "tool_selection_accuracy": self.tool_selection_accuracy,
            "parameter_accuracy": self.parameter_accuracy,
            "efficacy": self.efficacy,
            "expected_tools": self.expected_tools,
            "actual_tools": self.actual_tools,
            "milestones": self.milestones,
            "achieved_milestones": self.achieved_milestones,
            "notes": self.notes,
            "created_at": self.created_at,
        }


class EvaluationHarness:
    """Track evaluation episodes and compute aggregate metrics."""

    def __init__(self):
        self.db_path = os.path.join(DATABASE_DIR, "evaluation.db")
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS eval_results (
                episode_id TEXT PRIMARY KEY,
                task TEXT NOT NULL,
                expected_outcome TEXT,
                success INTEGER,
                progress_rate REAL,
                tool_selection_accuracy REAL,
                parameter_accuracy REAL,
                efficacy REAL,
                expected_tools TEXT DEFAULT '[]',
                actual_tools TEXT DEFAULT '[]',
                milestones TEXT DEFAULT '[]',
                achieved_milestones TEXT DEFAULT '[]',
                notes TEXT DEFAULT '',
                created_at REAL
            )
        """)
        conn.commit()
        conn.close()

    def record(self, result: EvalResult):
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT OR REPLACE INTO eval_results (episode_id, task, expected_outcome, success, progress_rate, tool_selection_accuracy, parameter_accuracy, efficacy, expected_tools, actual_tools, milestones, achieved_milestones, notes, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (result.episode_id, result.task, result.expected_outcome, int(result.success),
             result.progress_rate, result.tool_selection_accuracy, result.parameter_accuracy,
             result.efficacy, json.dumps(result.expected_tools), json.dumps(result.actual_tools),
             json.dumps(result.milestones), json.dumps(result.achieved_milestones),
             result.notes, result.created_at)
        )
        conn.commit()
        conn.close()

    def get_metrics(self) -> Dict[str, Any]:
        """Compute aggregate evaluation metrics."""
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute("SELECT * FROM eval_results").fetchall()
        conn.close()

        if not rows:
            return {
                "total_episodes": 0,
                "success_rate": 0.0,
                "avg_progress_rate": 0.0,
                "avg_tool_selection_accuracy": 0.0,
                "avg_parameter_accuracy": 0.0,
                "avg_efficacy": 0.0,
            }

        cols = ["episode_id", "task", "expected_outcome", "success", "progress_rate",
                "tool_selection_accuracy", "parameter_accuracy", "efficacy",
                "expected_tools", "actual_tools", "milestones", "achieved_milestones",
                "notes", "created_at"]

        total = len(rows)
        successes = sum(1 for r in rows if r[3])
        avg_progress = sum(r[4] for r in rows) / total
        avg_tool_sel = sum(r[5] for r in rows) / total
        avg_param = sum(r[6] for r in rows) / total
        avg_efficacy = sum(r[7] for r in rows) / total

        return {
            "total_episodes": total,
            "success_rate": round(successes / total, 3),
            "avg_progress_rate": round(avg_progress, 3),
            "avg_tool_selection_accuracy": round(avg_tool_sel, 3),
            "avg_parameter_accuracy": round(avg_param, 3),
            "avg_efficacy": round(avg_efficacy, 3),
        }

    def list_episodes(self, limit: int = 50) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute("SELECT * FROM eval_results ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        conn.close()

        cols = ["episode_id", "task", "expected_outcome", "success", "progress_rate",
                "tool_selection_accuracy", "parameter_accuracy", "efficacy",
                "expected_tools", "actual_tools", "milestones", "achieved_milestones",
                "notes", "created_at"]

        episodes = []
        for row in rows:
            data = dict(zip(cols, row))
            episodes.append({
                "episode_id": data["episode_id"],
                "task": data["task"],
                "success": bool(data["success"]),
                "progress_rate": data["progress_rate"],
                "tool_selection_accuracy": data["tool_selection_accuracy"],
                "parameter_accuracy": data["parameter_accuracy"],
                "efficacy": data["efficacy"],
                "expected_tools": json.loads(data["expected_tools"]),
                "actual_tools": json.loads(data["actual_tools"]),
                "notes": data["notes"],
            })
        return episodes


# ============================================
# EVALUATION HELPERS (scoring functions)
# ============================================

def score_success(expected_outcome: str, actual_output: str) -> bool:
    """Binary success: did the agent reach the expected outcome?"""
    # Keyword overlap heuristic (production: use LLM judge)
    expected_keywords = set(expected_outcome.lower().split())
    actual_keywords = set(actual_output.lower().split())
    if not expected_keywords:
        return False
    overlap = len(expected_keywords & actual_keywords) / len(expected_keywords)
    return overlap >= 0.5


def score_progress(milestones: List[str], achieved: List[str]) -> float:
    """Stepwise progress rate: fraction of milestones achieved."""
    if not milestones:
        return 0.0
    achieved_set = set(achieved)
    return len([m for m in milestones if m in achieved_set]) / len(milestones)


def score_tool_selection(expected_tools: List[str], actual_tools: List[str]) -> float:
    """Tool selection accuracy: fraction of expected tools used."""
    if not expected_tools:
        return 1.0
    actual_set = set(actual_tools)
    return len([t for t in expected_tools if t in actual_set]) / len(expected_tools)


def score_parameter_accuracy(expected_args: Dict[str, Any], actual_args: Dict[str, Any]) -> float:
    """Parameter accuracy: fraction of correct argument values."""
    if not expected_args:
        return 1.0
    correct = sum(1 for k, v in expected_args.items() if actual_args.get(k) == v)
    return correct / len(expected_args)


def score_efficacy(before_wrong: bool, after_correct: bool) -> float:
    """Efficacy: did the tool call improve the answer (wrong → right)?"""
    if before_wrong and after_correct:
        return 1.0  # Tool fixed the answer
    if not before_wrong and after_correct:
        return 0.5  # Already correct, tool didn't hurt
    return 0.0  # Tool didn't help


# Global instance
_harness = None

def get_eval_harness() -> EvaluationHarness:
    global _harness
    if _harness is None:
        _harness = EvaluationHarness()
    return _harness
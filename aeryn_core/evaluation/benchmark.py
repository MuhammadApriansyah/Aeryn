"""Benchmark Suite — runnable eval scenarios with gold annotations.

Berdasarkan riset: benchmark harus punya gold tool paths + milestones,
bukan cuma binary success. Setiap scenario punya:
- task (prompt)
- expected_outcome (gold answer keywords)
- milestones (subgoals untuk progress rate)
- expected_tools (gold tool path)
- gold_args (parameter accuracy check)
"""

from typing import Dict, Any, List
from dataclasses import dataclass, field


@dataclass
class BenchmarkScenario:
    """A single eval scenario with gold annotations."""
    id: str
    task: str
    expected_outcome: str
    milestones: List[str] = field(default_factory=list)
    expected_tools: List[str] = field(default_factory=list)
    gold_args: Dict[str, Any] = field(default_factory=dict)
    category: str = "general"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "task": self.task,
            "expected_outcome": self.expected_outcome,
            "milestones": self.milestones,
            "expected_tools": self.expected_tools,
            "gold_args": self.gold_args,
            "category": self.category,
        }


# Gold-annotated benchmark scenarios (real, deterministic, no test doubles)
BENCHMARK_SCENARIOS: List[BenchmarkScenario] = [
    # Tool-use scenarios
    BenchmarkScenario(
        id="bash_echo",
        task="Run the shell command 'echo hello' and tell me the output",
        expected_outcome="hello",
        milestones=["identify bash tool", "execute echo", "report output"],
        expected_tools=["bash"],
        gold_args={"command": "echo hello"},
        category="tool_use",
    ),
    BenchmarkScenario(
        id="file_read",
        task="Read the file at /tmp/test.txt and summarize it",
        expected_outcome="test content",
        milestones=["identify file_read", "read file", "summarize"],
        expected_tools=["file_read"],
        gold_args={"path": "/tmp/test.txt"},
        category="tool_use",
    ),
    BenchmarkScenario(
        id="web_search",
        task="Search the web for information about Python programming",
        expected_outcome="python programming",
        milestones=["identify web_search", "search", "report results"],
        expected_tools=["web_search"],
        gold_args={"query": "Python programming"},
        category="tool_use",
    ),

    # Calculation scenarios
    BenchmarkScenario(
        id="calculate",
        task="Calculate 15 * 7 + 3",
        expected_outcome="108",
        milestones=["identify calculate", "compute", "report answer"],
        expected_tools=["calculate"],
        gold_args={"expression": "15 * 7 + 3"},
        category="calculation",
    ),

    # Reasoning scenarios (no tool needed)
    BenchmarkScenario(
        id="reasoning_no_tool",
        task="Explain what 2 + 2 equals",
        expected_outcome="4",
        milestones=["understand question", "compute", "answer"],
        expected_tools=[],  # no tool required
        category="reasoning",
    ),

    # Multi-step scenarios
    BenchmarkScenario(
        id="multi_step",
        task="Search for 'artificial intelligence' then calculate 10 * 10",
        expected_outcome="artificial intelligence 100",
        milestones=["search AI", "calculate", "combine results"],
        expected_tools=["web_search", "calculate"],
        category="multi_step",
    ),
]


class BenchmarkSuite:
    """Manages benchmark scenarios."""

    def __init__(self):
        self.scenarios = {s.id: s for s in BENCHMARK_SCENARIOS}

    def list_scenarios(self) -> List[Dict[str, Any]]:
        return [s.to_dict() for s in self.scenarios.values()]

    def get_scenario(self, scenario_id: str) -> BenchmarkScenario:
        return self.scenarios.get(scenario_id)

    def get_by_category(self, category: str) -> List[BenchmarkScenario]:
        return [s for s in self.scenarios.values() if s.category == category]

    def run_suite(self, agent_runner) -> List[Dict[str, Any]]:
        """Run all scenarios through an agent_runner (async callable).
        Returns evaluation results. This is a REAL evaluation, not a test double."""
        import asyncio
        results = []

        async def _run():
            for scenario in self.scenarios.values():
                # Run agent
                output = await agent_runner(scenario.task)

                # Score
                from aeryn_core.evaluation.harness import (
                    score_success, score_progress, score_tool_selection
                )
                content = output.get("content", "")
                success = score_success(scenario.expected_outcome, content)
                progress = score_progress(scenario.milestones, [])  # milestone tracking needs instrumentation
                tool_sel = score_tool_selection(scenario.expected_tools, output.get("actual_tools", []))

                results.append({
                    "scenario": scenario.id,
                    "category": scenario.category,
                    "success": success,
                    "progress_rate": progress,
                    "tool_selection_accuracy": tool_sel,
                })

        asyncio.get_event_loop().run_until_complete(_run())
        return results

    def category_coverage(self) -> Dict[str, int]:
        """Count scenarios per category."""
        coverage = {}
        for s in self.scenarios.values():
            coverage[s.category] = coverage.get(s.category, 0) + 1
        return coverage


# Global suite
_suite = None

def get_benchmark_suite() -> BenchmarkSuite:
    global _suite
    if _suite is None:
        _suite = BenchmarkSuite()
    return _suite
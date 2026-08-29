"""Test UnifiedCognitiveOrchestrator — DAG, divisions, prompt compilation."""
import os
import sys
from unittest.mock import patch, MagicMock, PropertyMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock numpy before importing anything that uses it
sys.modules['numpy'] = MagicMock()
sys.modules['numpy.linalg'] = MagicMock()

# Mock aeryn_native before importing orchestrator
sys.modules['aeryn_native'] = MagicMock()


class TestDirectedAcyclicGraphWorkflowEngine:
    """Tests for DAG workflow engine."""

    def test_init(self):
        from aeryn_core.utils.workflow_dag import DirectedAcyclicGraphWorkflowEngine
        dag = DirectedAcyclicGraphWorkflowEngine()
        assert dag.nodes == {}
        assert dag.workflow_execution_logs == []

    def test_register_node(self):
        from aeryn_core.utils.workflow_dag import DirectedAcyclicGraphWorkflowEngine
        dag = DirectedAcyclicGraphWorkflowEngine()
        dag.register_cognitive_task_node("TASK_A", division_code=1, fsm_gate_code=0)
        assert "TASK_A" in dag.nodes
        assert dag.nodes["TASK_A"].division_code == 1
        assert dag.nodes["TASK_A"].fsm_gate_code == 0

    def test_register_duplicate_node(self):
        from aeryn_core.utils.workflow_dag import DirectedAcyclicGraphWorkflowEngine
        dag = DirectedAcyclicGraphWorkflowEngine()
        dag.register_cognitive_task_node("TASK_A", 1, 0)
        dag.register_cognitive_task_node("TASK_A", 2, 1)  # Should not overwrite
        assert dag.nodes["TASK_A"].division_code == 1

    def test_bind_dependency(self):
        from aeryn_core.utils.workflow_dag import DirectedAcyclicGraphWorkflowEngine
        dag = DirectedAcyclicGraphWorkflowEngine()
        dag.register_cognitive_task_node("TASK_A", 1, 0)
        dag.register_cognitive_task_node("TASK_B", 2, 1)
        dag.bind_task_dependency("TASK_B", "TASK_A")
        assert "TASK_A" in dag.nodes["TASK_B"].dependencies

    def test_bind_dependency_missing_node(self):
        from aeryn_core.utils.workflow_dag import DirectedAcyclicGraphWorkflowEngine
        dag = DirectedAcyclicGraphWorkflowEngine()
        dag.register_cognitive_task_node("TASK_A", 1, 0)
        # Should not raise even if target doesn't exist
        dag.bind_task_dependency("TASK_B", "TASK_A")
        dag.bind_task_dependency("TASK_A", "NONEXISTENT")

    def test_topological_sort(self):
        from aeryn_core.utils.workflow_dag import DirectedAcyclicGraphWorkflowEngine
        dag = DirectedAcyclicGraphWorkflowEngine()
        dag.register_cognitive_task_node("TASK_A", 1, 0)
        dag.register_cognitive_task_node("TASK_B", 2, 1)
        dag.register_cognitive_task_node("TASK_C", 3, 2)
        dag.bind_task_dependency("TASK_B", "TASK_A")
        dag.bind_task_dependency("TASK_C", "TASK_B")
        result = dag.topological_sort_evaluation_path()
        assert isinstance(result, list)
        assert "TASK_A" in result
        assert "TASK_B" in result
        assert "TASK_C" in result


class TestCognitiveTaskNode:
    """Tests for CognitiveTaskNode."""

    def test_init(self):
        from aeryn_core.utils.workflow_dag import CognitiveTaskNode
        node = CognitiveTaskNode("NODE_1", division_code=2, fsm_gate_code=1)
        assert node.node_id == "NODE_1"
        assert node.division_code == 2
        assert node.fsm_gate_code == 1
        assert node.dependencies == []
        assert node.execution_status == "PENDING_SATELLITE"


class TestUnifiedCognitiveOrchestrator:
    """Tests for UnifiedCognitiveOrchestrator with mocked dependencies."""

    def test_init(self):
        from aeryn_core.platform.orchestrator import UnifiedCognitiveOrchestrator
        orch = UnifiedCognitiveOrchestrator()
        assert orch.dimension == 384
        assert orch.idle_threshold == 10
        assert orch.absolute_threshold == 0.70
        assert orch.rust_brain is not None
        assert orch.guardrail is not None
        assert orch.div1_creative is not None
        assert orch.div2_psych is not None
        assert orch.div3_reasoning is not None
        assert orch.div4_gov is not None
        assert orch.div5_infra is not None

    def test_init_custom_params(self):
        from aeryn_core.platform.orchestrator import UnifiedCognitiveOrchestrator
        orch = UnifiedCognitiveOrchestrator(dimension=256, idle_threshold=5, absolute_threshold=0.8)
        assert orch.dimension == 256
        assert orch.idle_threshold == 5
        assert orch.absolute_threshold == 0.8

    def test_dag_engine_initialized(self):
        from aeryn_core.platform.orchestrator import UnifiedCognitiveOrchestrator
        orch = UnifiedCognitiveOrchestrator()
        assert orch.dag_engine is not None
        # Should have 5 task nodes registered
        assert len(orch.dag_engine.nodes) == 5

    def test_workflow_anchors_initially_empty(self):
        from aeryn_core.platform.orchestrator import UnifiedCognitiveOrchestrator
        orch = UnifiedCognitiveOrchestrator()
        assert orch.workflow_anchors == []

    def test_cached_blackboard_initially_empty(self):
        from aeryn_core.platform.orchestrator import UnifiedCognitiveOrchestrator
        orch = UnifiedCognitiveOrchestrator()
        assert orch.cached_shared_blackboard == "{}"
        assert orch.cached_active_gate_mode == 3

    def test_subsystems_initialized(self):
        from aeryn_core.platform.orchestrator import UnifiedCognitiveOrchestrator
        orch = UnifiedCognitiveOrchestrator()
        assert orch.context_router is not None
        assert orch.event_bus is not None
        assert orch.memory_pool is not None
        assert orch.cog_mem is not None
        assert orch.bica_bridge is not None
        assert orch.reconsideration_guard is not None
        assert orch.meta_evolution is not None
        assert orch.inference_budget is not None
        assert orch.latent_value is not None
        assert orch.context_pruner is not None
        assert orch.swarm_handler is not None
        assert orch.memory_bridge is not None

    def test_register_agent_workflow_anchor(self):
        from aeryn_core.platform.orchestrator import UnifiedCognitiveOrchestrator
        import asyncio
        orch = UnifiedCognitiveOrchestrator()
        result = asyncio.get_event_loop().run_until_complete(
            orch.register_agent_workflow_anchor(
                "TEST_EVENT",
                "Test description",
                {"key": "value"}
            )
        )
        assert result is True
        assert len(orch.workflow_anchors) == 1
        assert orch.workflow_anchors[0]["event_type"] == "TEST_EVENT"
        assert orch.workflow_anchors[0]["status"] == "ACTIVE_ANCHOR"

    def test_register_multiple_anchors(self):
        from aeryn_core.platform.orchestrator import UnifiedCognitiveOrchestrator
        import asyncio
        orch = UnifiedCognitiveOrchestrator()
        for i in range(3):
            asyncio.get_event_loop().run_until_complete(
                orch.register_agent_workflow_anchor(
                    f"EVENT_{i}",
                    f"Description {i}",
                    {"index": i}
                )
            )
        assert len(orch.workflow_anchors) == 3

    def test_compile_stateful_system_prompt(self):
        from aeryn_core.platform.orchestrator import UnifiedCognitiveOrchestrator
        orch = UnifiedCognitiveOrchestrator()
        result = orch.compile_stateful_system_prompt(
            session_id="test_session",
            base_character_prompt="You are a helpful assistant.",
            user_prompt="Hello, how are you?",
            mock_history_logs=[],
            open_tasks=[]
        )
        assert isinstance(result, str)
        assert len(result) > 0

    def test_compile_stateful_system_prompt_with_history(self):
        from aeryn_core.platform.orchestrator import UnifiedCognitiveOrchestrator
        orch = UnifiedCognitiveOrchestrator()
        result = orch.compile_stateful_system_prompt(
            session_id="test_session",
            base_character_prompt="You are Aeryn.",
            user_prompt="Tell me about Python",
            mock_history_logs=["user: Hello", "aeryn: Hi there!"],
            open_tasks=["Learn Python"]
        )
        assert isinstance(result, str)
        assert len(result) > 0

    def test_digest_external_llm_response(self):
        from aeryn_core.platform.orchestrator import UnifiedCognitiveOrchestrator
        orch = UnifiedCognitiveOrchestrator()
        # First compile a prompt to set internal state
        orch.compile_stateful_system_prompt(
            session_id="test_session",
            base_character_prompt="You are Aeryn.",
            user_prompt="Hello",
            mock_history_logs=[],
            open_tasks=[]
        )
        result = orch.digest_external_llm_response(
            session_id="test_session",
            user_prompt="Hello",
            raw_llm_output_text="Hi! How can I help you today?"
        )
        assert isinstance(result, dict)
        assert "status" in result
        assert "cleaned_response_text" in result
        assert result["status"] == "SUCCESS_COMMIT"

    def test_digest_with_think_tags(self):
        from aeryn_core.platform.orchestrator import UnifiedCognitiveOrchestrator
        orch = UnifiedCognitiveOrchestrator()
        orch.compile_stateful_system_prompt(
            session_id="test_session",
            base_character_prompt="You are Aeryn.",
            user_prompt="Hello",
            mock_history_logs=[],
            open_tasks=[]
        )
        result = orch.digest_external_llm_response(
            session_id="test_session",
            user_prompt="Hello",
            raw_llm_output_text="<think>Let me think...</think>Here is my response."
        )
        assert "think" not in result["cleaned_response_text"].lower()

    def test_digest_returns_ledger_audit(self):
        from aeryn_core.platform.orchestrator import UnifiedCognitiveOrchestrator
        orch = UnifiedCognitiveOrchestrator()
        orch.compile_stateful_system_prompt(
            session_id="test_session",
            base_character_prompt="You are Aeryn.",
            user_prompt="Hello",
            mock_history_logs=[],
            open_tasks=[]
        )
        result = orch.digest_external_llm_response(
            session_id="test_session",
            user_prompt="Hello",
            raw_llm_output_text="Response text"
        )
        assert "accounting_ledger_audit" in result
        assert "cog_mem_lifecycle_telemetry" in result
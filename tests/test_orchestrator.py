#!/usr/bin/env python3
"""Test DAG workflow engine dan CognitiveTaskNode."""
import os
import sys
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock numpy sebelum import
sys.modules['numpy'] = MagicMock()
sys.modules['numpy.linalg'] = MagicMock()
sys.modules['aeryn_native'] = MagicMock()


class TestDirectedAcyclicGraphWorkflowEngine:
    def test_init(self):
        from aeryn_core.utils.workflow_dag import DirectedAcyclicGraphWorkflowEngine
        dag = DirectedAcyclicGraphWorkflowEngine()
        assert dag.nodes == {}
    
    def test_register_node(self):
        from aeryn_core.utils.workflow_dag import DirectedAcyclicGraphWorkflowEngine
        dag = DirectedAcyclicGraphWorkflowEngine()
        dag.register_cognitive_task_node("TASK_A", division_code=1, fsm_gate_code=0)
        assert "TASK_A" in dag.nodes
        assert dag.nodes["TASK_A"].division_code == 1
    
    def test_topological_sort(self):
        from aeryn_core.utils.workflow_dag import DirectedAcyclicGraphWorkflowEngine
        dag = DirectedAcyclicGraphWorkflowEngine()
        dag.register_cognitive_task_node("TASK_A", 1, 0)
        dag.register_cognitive_task_node("TASK_B", 2, 1)
        dag.bind_task_dependency("TASK_B", "TASK_A")
        result = dag.topological_sort_evaluation_path()
        assert "TASK_A" in result
        assert "TASK_B" in result

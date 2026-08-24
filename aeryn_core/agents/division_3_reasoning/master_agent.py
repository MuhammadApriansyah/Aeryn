import json
import time
from aeryn_core.agents.division_3_reasoning.middleware import ReasoningDivisionMiddleware
from aeryn_core.agents.division_3_reasoning.sub_agent_mcts.agent import SubAgentMonteCarloTreeSearchScheduler
from aeryn_core.agents.division_3_reasoning.sub_agent_fol.agent import SubAgentFirstOrderLogicPredicateGate
from aeryn_core.agents.division_3_reasoning.sub_agent_critique.agent import SubAgentAdvisoryBoardMonologueCritique
from aeryn_core.agents.division_3_reasoning.sub_agent_graph.agent import SubAgentEpistemicGraphTraverser

class NeuroSymbolicReasoningDirector:
    def __init__(self, dimension: int = 384, confidence_floor: float = 0.70):
        self.dimension = dimension
        self.confidence_floor = confidence_floor
        self.jepa_target_mode = "V-JEPA"
        
        self.middleware = ReasoningDivisionMiddleware()
        self.mcts_scheduler = SubAgentMonteCarloTreeSearchScheduler(confidence_floor)
        self.fol_gate = SubAgentFirstOrderLogicPredicateGate()
        self.critique_board = SubAgentAdvisoryBoardMonologueCritique()
        self.graph_traverser = SubAgentEpistemicGraphTraverser()

    def calculate_mdl(self, program_graph: str) -> float:
        if not program_graph: return 0.0
        return float(len(program_graph.encode('utf-8')) * 0.55)

    def compile_reasoning_vector_payload(self, proposition_id: str, program_graph: str, exploration_depth: int, rust_brain_instance: any = None, session_id: str = "GLOBAL_SESSION") -> str:
        middleware_res = self.middleware.enforce_temporal_compute_budget(exploration_depth, False)
        target_depth = middleware_res["sanitized_exploration_depth"]

        mcts_res = self.mcts_scheduler.execute_sub_brain_reasoning(proposition_id, target_depth)
        fol_res = self.fol_gate.execute_sub_brain_reasoning(proposition_id)
        critique_res = self.critique_board.execute_sub_brain_reasoning(mcts_res["mcts_passed"], fol_res["fol_consistent"])
        
        associated_memories = []
        if rust_brain_instance is not None:
            try:
                raw_neighbors = rust_brain_instance.traverse_associated_neighbors(session_id, proposition_id)
                associated_memories = raw_neighbors if isinstance(raw_neighbors, list) else []
                if associated_memories:
                    # KOREKSI INDENTASI V17.3: Gunakan pass agar blok if tetap legal secara sintaksis
                    pass
            except Exception as e:
                # KOREKSI INDENTASI V17.3: Gunakan pass agar blok except tetap legal secara sintaksis
                pass

        mdl_score = self.calculate_mdl(program_graph)
        
        reasoning_context_payload = {
            "event_class": "REASONING_LOGIC_PROPOSITION",
            "proposition_id": proposition_id,
            "mdl_compression_score": round(mdl_score, 4),
            "mcts_score": mcts_res["mcts_score"],
            "anti_hallucination_gate_passed": critique_res["global_clearance"],
            "associated_graph_memories": associated_memories,
            "jepa_alignment_mode": self.jepa_target_mode,
            "advisory_verdict": critique_res["advisory_verdict"],
            "compiled_timestamp": int(time.time())
        }
        
        return json.dumps(reasoning_context_payload)


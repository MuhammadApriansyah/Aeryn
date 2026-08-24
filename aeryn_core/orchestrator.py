import json
import time
from aeryn_core.agents.division_1_creative.master_agent import CreativeDivisionDirector
from aeryn_core.agents.division_2_psych.master_agent import PsychologicalAmigdalaOrchestrator
from aeryn_core.agents.division_3_reasoning.master_agent import NeuroSymbolicReasoningDirector
from aeryn_core.agents.division_4_gov.master_agent import SovereignGovernanceDirector
from aeryn_core.agents.division_5_infra.master_agent import TransactionConsensusDirector
from aeryn_core.utils.guardrails import CognitiveGuardrailEngine
from aeryn_core.utils.workflow_dag import DirectedAcyclicGraphWorkflowEngine
from aeryn_core.utils.dynamic_router import EpistemicContextRouter
from aeryn_core.utils.event_bus import CognitiveAsynchronousEventBus
from aeryn_core.utils.memory_pool import StatefulVolatileMemoryPool
from aeryn_core.utils.cog_mem_lifecycle import CognitiveSustainedMemoryLifecycle
from aeryn_core.utils.bica_alignment import BidirectionalCognitiveAlignmentBridge
from aeryn_core.utils.reconsideration_guard import AgenticReconsiderationGuard
from aeryn_core.utils.meta_evolution import MetaPromptEvolutionDirector
from aeryn_core.utils.adaptive_inference import AdaptiveInferenceBudgetController

# EKSPANSI COGOS V23.0 RESMI: INJEKSI INTEGRATED INFERENCE-TIME SWARM SEALS
from aeryn_core.utils.latent_value import LatentValueEvaluationNode
from aeryn_core.utils.context_pruner import VerifiableContextCompactor
from aeryn_core.utils.swarm_convergence import SwarmConvergenceConsensusHandler

from aeryn_native import PyUnifiedCognitiveSystem

class UnifiedCognitiveOrchestrator:
    def __init__(self, dimension: int = 384, idle_threshold: int = 10, absolute_threshold: float = 0.70):
        self.dimension = dimension
        self.idle_threshold = idle_threshold
        self.absolute_threshold = absolute_threshold
        
        self.rust_brain = PyUnifiedCognitiveSystem(dimension, idle_threshold)
        self.guardrail = CognitiveGuardrailEngine(variance_threshold=-1.0)
        
        self.div1_creative = CreativeDivisionDirector(dimension)
        self.div2_psych = PsychologicalAmigdalaOrchestrator(dimension)
        self.div3_reasoning = NeuroSymbolicReasoningDirector(dimension)
        self.div4_gov = SovereignGovernanceDirector(dimension)
        self.div5_infra = TransactionConsensusDirector()
        
        self.workflow_anchors = []
        self.cached_shared_blackboard = "{}"
        self.cached_active_gate_mode = 3

        self.context_router = EpistemicContextRouter(dimension)
        self.event_bus = CognitiveAsynchronousEventBus()
        self.memory_pool = StatefulVolatileMemoryPool(capacity_limit=100)

        self.cog_mem = CognitiveSustainedMemoryLifecycle(long_term_threshold=0.70)
        self.bica_bridge = BidirectionalCognitiveAlignmentBridge(divergence_limit=0.60)
        self.reconsideration_guard = AgenticReconsiderationGuard(inertia_floor=0.40)
        self.meta_evolution = MetaPromptEvolutionDirector(friction_ceiling=0.80)
        self.inference_budget = AdaptiveInferenceBudgetController(high_effort_threshold=0.70)

        # INISIALISASI SUBSISTEM OPTIMASI PREFIX-LEVEL SWARM v23.0
        self.latent_value = LatentValueEvaluationNode(baseline_threshold=0.55)
        self.context_pruner = VerifiableContextCompactor(retention_limit=4096)
        self.swarm_handler = SwarmConvergenceConsensusHandler(agreement_floor=0.60)

        self.dag_engine = DirectedAcyclicGraphWorkflowEngine()
        self.dag_engine.register_cognitive_task_node("TASK_AMIGDALA_PSYCH", division_code=2, fsm_gate_code=1)
        self.dag_engine.register_cognitive_task_node("TASK_NEURO_SYMBOLIC_SEARCH", division_code=3, fsm_gate_code=2)
        self.dag_engine.register_cognitive_task_node("TASK_DEEPSEEK_INFERENCE", division_code=1, fsm_gate_code=3)
        self.dag_engine.register_cognitive_task_node("TASK_GOVERNANCE_CHECK", division_code=4, fsm_gate_code=4)
        self.dag_engine.register_cognitive_task_node("TASK_INFRA_LEDGER", division_code=5, fsm_gate_code=0)

        self.dag_engine.bind_task_dependency("TASK_NEURO_SYMBOLIC_SEARCH", "TASK_AMIGDALA_PSYCH")
        self.dag_engine.bind_task_dependency("TASK_DEEPSEEK_INFERENCE", "TASK_NEURO_SYMBOLIC_SEARCH")
        self.dag_engine.bind_task_dependency("TASK_GOVERNANCE_CHECK", "TASK_DEEPSEEK_INFERENCE")
        self.dag_engine.bind_task_dependency("TASK_INFRA_LEDGER", "TASK_GOVERNANCE_CHECK")

        # V24 REAL-MEMORY: jembatan memori nyata (embedding → Rust vault + graph)
        from aeryn_core.utils.memory_vault_bridge import MemoryVaultBridge
        self.memory_bridge = MemoryVaultBridge(rust_brain=self.rust_brain, dimension=dimension)

    async def register_agent_workflow_anchor(self, event_type: str, semantic_description: str, payload_config: dict) -> bool:
        try:
            anchor_node = {
                "event_type": event_type,
                "semantic_description": semantic_description,
                "payload_config": payload_config,
                "registered_timestamp": int(time.time()),
                "status": "ACTIVE_ANCHOR"
            }
            self.workflow_anchors.append(anchor_node)
            await self.event_bus.publish_cognitive_event("ANCHOR_REGISTERED", anchor_node)
            return True
        except Exception:
            return False

    def compile_stateful_system_prompt(self, session_id: str, base_character_prompt: str, user_prompt: str, mock_history_logs: list, open_tasks: list, external_preference_vector: dict = None) -> str:
        event_id = f"EVNT_STIMULUS_{int(time.time())}"

        # V24 REAL-DATA: psikologi menganalisis stimulus & history nyata (bukan mock_state)
        psych_results = self.div2_psych.compile_psychological_vector_payload(
            user_id=session_id, logs=mock_history_logs, open_tasks=open_tasks,
            current_stimulus=user_prompt
        )
        self.cached_shared_blackboard = psych_results["json_payload"]
        self.cached_active_gate_mode = psych_results["recommended_gate"]

        # V24 REAL-MEMORY: retrieval memori relevan dari Rust vault utk konteks prompt
        retrieved_memories = []
        try:
            hits = self.memory_bridge.retrieve(session_id, user_prompt, gate_mode=self.cached_active_gate_mode, top_k=4)
            retrieved_memories = [h.get("text", "") for h in hits if h.get("text")]
        except Exception:
            retrieved_memories = []

        parsed_bb = json.loads(self.cached_shared_blackboard)
        tensor_data = parsed_bb.get("emotional_tensor_snapshot", {})
        compassion_score = float(tensor_data.get("compassion", 0.5))
        stress_index = 1.0 - compassion_score
        
        reconsider_res = self.reconsideration_guard.evaluate_commitment_trajectory(
            session_id=session_id,
            new_user_stimulus=user_prompt,
            emotional_stress_index=stress_index
        )

        pref_vector = external_preference_vector if external_preference_vector else {"target_pragmatism": 0.80, "target_hostility": 0.20}
        bica_res = self.bica_bridge.execute_co_adaptation_step(
            session_id=session_id,
            external_preference_vector=pref_vector,
            internal_tensor_snapshot=tensor_data
        )

        routing_decision = self.context_router.compute_dynamic_routing_weight(
            session_id=session_id,
            semantic_complexity=float(len(user_prompt) / 1000.0),
            emotional_intensity=0.9 if self.cached_active_gate_mode == 0 else 0.2
        )

        risk_factor = 0.8 if self.cached_active_gate_mode == 0 else 0.1
        regime_res = self.inference_budget.regulate_inference_regime(
            session_id=session_id,
            prompt_complexity=routing_decision["calculated_priority"],
            security_risk=risk_factor
        )
        
        self.memory_pool.retain_volatile_state_segment(
            segment_key=f"ROUTING_{event_id}",
            data_payload={
                "routing": routing_decision, 
                "bica": bica_res, 
                "reconsideration": reconsider_res,
                "regime": regime_res
            },
            ttl_seconds=120
        )

        reasoning_json = self.div3_reasoning.compile_reasoning_vector_payload(
            event_id, user_prompt, exploration_depth=5, rust_brain_instance=self.rust_brain, session_id=session_id
        )
        reasoning_manifest = json.loads(reasoning_json)
        graph_memories_array = reasoning_manifest.get("associated_graph_memories", [])

        # V24: gabungkan hasil retrieval vektor dgn traversal graf
        all_memories = list(dict.fromkeys(graph_memories_array + retrieved_memories))

        environment_tools_manifest = self.rust_brain.compile_tools_manifest(session_id)

        # V24 REAL-MEMORY: suntikkan stimulus user ke vault agar retrieval berikutnya hidup
        try:
            self.memory_bridge.ingest_turn(session_id, "user", user_prompt)
            for log in (mock_history_logs or [])[-4:]:
                if isinstance(log, str) and ":" in log:
                    role, _, text = log.partition(":")
                    self.memory_bridge.ingest_turn(session_id, role.strip().lower() or "system", text.strip())
        except Exception:
            pass

        compiled_prompt = self.div1_creative.compile_sovereign_system_prompt_node(
            base_character_prompt=base_character_prompt,
            shared_blackboard_json=self.cached_shared_blackboard,
            associated_graph_memories=all_memories,
            tools_manifest=environment_tools_manifest
        )

        # V24 REAL-DATA: konteks psikologis eksplisit utk LLM (gate mode & afek user)
        bb = json.loads(self.cached_shared_blackboard)
        tensor = bb.get("emotional_tensor_snapshot", {})
        gate_labels = {0: "defensif-waspada", 1: "terfokus-tajam", 2: "tenang-terkendali", 3: "seimbang"}
        affect_ctx = (
            f"\n[COGNITIVE_STATE] mode={gate_labels.get(self.cached_active_gate_mode, 'seimbang')}"
            f" | user_affect={{valence:{bb.get('affect_analysis', {}).get('valence', 0)},"
            f" arousal:{bb.get('affect_analysis', {}).get('arousal', 0)}}}"
            f" | stress_index:{bb.get('stress_index', 0)}"
            " | Sesuaikan nada respons dengan state kognitif ini."
        )
        compiled_prompt += affect_ctx

        if retrieved_memories:
            mem_ctx = "\n[RELEVANT_MEMORY_CONTEXT]\n" + "\n".join(f"- {m}" for m in retrieved_memories[:4])
            compiled_prompt += mem_ctx
        
        compiled_prompt = self.meta_evolution.inject_evolutionary_bias_string(session_id, compiled_prompt)
        
        if bica_res["structural_action_required"] or reconsider_res["should_trigger_non_monotonic_step"]:
            compiled_prompt += f" [SYSTEM_COGNITIVE_CO_REGULATION: FORCE_ADAPTATION_INDEX_{bica_res['dynamic_adaptation_factor']}]"
            
        return compiled_prompt

    def digest_external_llm_response(self, session_id: str, user_prompt: str, raw_llm_output_text: str) -> dict:
        clean_narrative = raw_llm_output_text
        if "<think>" in raw_llm_output_text and "</think>" in raw_llm_output_text:
            parts = raw_llm_output_text.split("</think>")
            clean_narrative = parts[-1].strip()
        
        gov_results = self.div4_gov.verify_constitutional_compliance(
            user_prompt, clean_narrative, current_gate_mode=self.cached_active_gate_mode
        )

        if not gov_results["global_clearance"]:
            self.meta_evolution.record_reasoning_anomaly(
                session_id=session_id,
                division_code=4,
                failure_reason=gov_results["constitutional_status"],
                critical_score=0.45
            )

        infra_results = self.div5_infra.execute_infrastructure_accounting_sync(clean_narrative)

        parsed_bb = json.loads(self.cached_shared_blackboard)
        tensor_data = parsed_bb.get("emotional_tensor_snapshot", {})
        focus_score = float(tensor_data.get("focus", 0.5))
        
        mem_res = self.cog_mem.ingest_working_tokens(
            session_id=session_id,
            turn_id=f"TRN_{int(time.time())}",
            factual_content=clean_narrative,
            emotional_weight=focus_score
        )

        try:
            p_val = float(tensor_data.get("pragmatism", 1.0))
            h_val = float(tensor_data.get("hostility", 0.0))
            f_val = float(tensor_data.get("focus", 1.0))
            c_val = float(tensor_data.get("compassion", 0.0))
            self.rust_brain.save_affective_checkpoint(session_id, p_val, h_val, f_val, c_val)
            
            if mem_res["delegation_required"]:
                self.rust_brain.inject_epistemic_graph_node(session_id, "CONSOLIDATED_FACT", clean_narrative[:50])
        except Exception:
            pass

        # V24 REAL-MEMORY: respons LLM juga masuk vault → retrieval dua arah
        try:
            self.memory_bridge.ingest_turn(session_id, "aeryn", clean_narrative)
        except Exception:
            pass

        return {
            "status": "SUCCESS_COMMIT",
            "cleaned_response_text": clean_narrative,
            "accounting_ledger_audit": json.loads(infra_results["infra_json_payload"]),
            "cog_mem_lifecycle_telemetry": mem_res
        }

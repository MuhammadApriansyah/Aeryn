pub mod multi_epoch_broadcaster;
pub mod lyapunov_governor;

use std::time::{SystemTime, UNIX_EPOCH};
use crate::vector_engine::mod_engine::CoreCognitiveEngine;

pub struct MetabolicTickState {
    pub current_active_thought: String,
    pub focus_of_attention: String,
    pub cognitive_memory_load: f32,
    pub emotional_valence: lyapunov_governor::SovereignAffectiveTensor,
    pub last_tick_timestamp: u64,
}

pub struct MetabolismEngine {
    pub state: MetabolicTickState,
    pub broadcaster: multi_epoch_broadcaster::MultiEpochBroadcaster,
    pub governor: lyapunov_governor::LyapunovHomeostaticGovernor,
    pub idle_threshold_seconds: u64,
    pub current_epoch: u64,
}

impl MetabolismEngine {
    pub fn new(idle_threshold: u64) -> Self {
        let initial_affective = lyapunov_governor::SovereignAffectiveTensor {
            pragmatism: 1.0,
            hostility: 0.0,
            focus: 1.0,
            compassion: 0.0,
        };

        let initial_state = MetabolicTickState {
            current_active_thought: "SYSTEM_INITIALIZATION_SUCCESSFUL".to_string(),
            focus_of_attention: "USER_INTERFACE_MONITOR".to_string(),
            cognitive_memory_load: 0.10,
            emotional_valence: initial_affective,
            last_tick_timestamp: SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs(),
        };

        Self {
            state: initial_state,
            broadcaster: multi_epoch_broadcaster::MultiEpochBroadcaster::new(),
            governor: lyapunov_governor::LyapunovHomeostaticGovernor::new(0.90),
            idle_threshold_seconds: idle_threshold,
            current_epoch: 0,
        }
    }

    pub fn execute_metabolic_tick(&mut self, inbound_stimulus_length: usize) -> Result<(), String> {
        let current_time = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs();
        self.state.last_tick_timestamp = current_time;
        self.current_epoch += 1;

        let load_delta = (inbound_stimulus_length as f32) / 5000.0;
        self.state.cognitive_memory_load = (self.state.cognitive_memory_load + load_delta).min(1.0);

        self.state.emotional_valence = self.governor.compute_homeostatic_damping(
            &self.state.emotional_valence, 
            self.state.cognitive_memory_load
        );

        if self.state.cognitive_memory_load > 0.90 {
            self.state.current_active_thought = "COGNITIVE_OVERLOAD_PREVENTION_ACTIVATED".to_string();
            let _ = self.broadcaster.broadcast_to_timeline("ALPHA", self.current_epoch, "{\"status\":\"STRESS_ALERT\"}".to_string());
            return Err("Metabolic Warning: System cognitive memory load exceeded safety threshold.".to_string());
        }

        Ok(())
    }

    pub async fn execute_digital_dreaming_consolidation(
        &mut self,
        vector_engine: &CoreCognitiveEngine,
        current_time: u64,
    ) -> Result<usize, String> {
        let mut vault = vector_engine.database_vault.lock().map_err(|e| e.to_string())?;
        let mut episodic_indices = Vec::new();

        for (idx, event) in vault.iter().enumerate() {
            if event.event_type == "EPISODIC" {
                let age = current_time.saturating_sub(event.timestamp);
                if age >= self.idle_threshold_seconds {
                    episodic_indices.push(idx);
                }
            }
        }

        if episodic_indices.is_empty() {
            return Ok(0);
        }

        let mut consolidated_count = 0;
        let mut processed_flags = vec![false; vault.len()];
        
        // KUNCI MULTI-SESSION MIMPI: Tetapkan pengenal jembatan untuk fase asimilasi biner
        let active_dream_session = "GLOBAL_SESSION";

        for &target_idx in &episodic_indices {
            if processed_flags[target_idx] { continue; }

            let mut cluster_group = vec![target_idx];
            processed_flags[target_idx] = true;

            let packed_target = vector_engine.lattice_quantizer.execute_lattice_compression(&vault[target_idx].embedding)?;

            for &compare_idx in &episodic_indices {
                if processed_flags[compare_idx] { continue; }
                
                let packed_compare = vector_engine.lattice_quantizer.execute_lattice_compression(&vault[compare_idx].embedding)?;
                
                if let Ok(score) = vector_engine.lattice_quantizer.compute_bitwise_hamming_distance(&packed_target, &packed_compare) {
                    if score >= 0.85 {
                        cluster_group.push(compare_idx);
                        processed_flags[compare_idx] = true;
                    }
                }
            }

            if !cluster_group.is_empty() {
                let primary_idx = cluster_group[0];
                vault[primary_idx].event_type = "SEMANTIC".to_string();
                vault[primary_idx].ttl_seconds = 0;
                
                let text_payload = vault[primary_idx].context_payload.to_lowercase();
                let source_entity = "aeryn";
                
                // PERBAIKAN PARAMETER V15: Suntikkan active_dream_session sebagai parameter pertama yang legal
                let _ = vector_engine.epistemic_graph.upsert_memory_node_isolated(active_dream_session, source_entity, "CHARACTER");
                
                if text_payload.contains("tactical") || text_payload.contains("baseline") {
                    let target_entity = "tactical_baseline";
                    let _ = vector_engine.epistemic_graph.upsert_memory_node_isolated(active_dream_session, target_entity, "PROTOCOL");
                    let _ = vector_engine.epistemic_graph.connect_semantic_edge_isolated(active_dream_session, source_entity, target_entity, "ENFORCES", 1.0);
                }
                if text_payload.contains("lockdown") || text_payload.contains("sector") {
                    let target_entity = "sector_lockdown";
                    let _ = vector_engine.epistemic_graph.upsert_memory_node_isolated(active_dream_session, target_entity, "CONTINGENCY");
                    let _ = vector_engine.epistemic_graph.connect_semantic_edge_isolated(active_dream_session, source_entity, target_entity, "TRIGGERS", 0.95);
                }

                let _ = vector_engine.serialize_to_mandated_disk(&vault[primary_idx]);
                consolidated_count += 1;

                for &idx in cluster_group.iter().skip(1) {
                    vault[idx].event_type = "PRUNED_SYNTHESIS_VOID".to_string();
                }
            }
        }

        vault.retain(|event| event.event_type != "PRUNED_SYNTHESIS_VOID");

        if consolidated_count > 0 {
            self.state.cognitive_memory_load = (self.state.cognitive_memory_load - 0.40).max(0.10);
            self.state.current_active_thought = "EPISTEMIC_GRAPH_SYNTHESIS_COMPLETED".to_string();
            vector_engine.gated_router.flush_load_balancer_tracker();
            let _ = self.broadcaster.broadcast_to_timeline("GAMMA", self.current_epoch, "{\"event\":\"GRAPH_RECONCILIATION_SUCCESS\"}".to_string());
        }

        Ok(consolidated_count)
    }
}


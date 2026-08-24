pub mod binary_lattice;
pub mod dynamic_hnsw_router;
pub mod residual_cache;
pub mod telemetry_monitor;
pub mod ring_buffer_bus;
pub mod epistemic_graph;
pub mod persistence_store;
pub mod tool_binder;
pub mod tool_executor;
pub mod state_machine; // DAFTARKAN MODUL BARU DI SINI

use std::fs::{self, File};
use std::io::Write;

#[derive(Clone, Debug)]
pub struct CognitiveEvent {
    pub event_id: String,
    pub event_type: String,      
    pub embedding: Vec<f32>,     
    pub context_payload: String, 
    pub timestamp: u64,
    pub ttl_seconds: u64,        
}

#[derive(Clone, Copy, Debug)]
pub enum EmotionalGateMode {
    DefensiveHostile,
    HyperFocused,
    SuppressedCompassion,
    BalancedDefault,
}

pub struct CoreCognitiveEngine {
    pub dimension: usize,
    pub lattice_quantizer: binary_lattice::BinaryLatticeQuantizer,
    pub gated_router: dynamic_hnsw_router::DynamicHnswRouter,
    pub residual_guard: residual_cache::ResidualCacheBuffer,
    pub epistemic_graph: epistemic_graph::EpistemicWorldGraph,
    pub persistence_guard: persistence_store::PersistenceStoreManager,
    pub tool_binder: tool_binder::CoreEnvironmentToolBinder,
    pub tool_executor: tool_executor::CoreEnvironmentToolExecutor,
    pub state_machine: state_machine::DeterministicCognitiveStateMachine, // TANAMKAN KENDALI STATUS v17
    pub database_vault: std::sync::Mutex<Vec<CognitiveEvent>>,
    pub mandated_path: String,
}

impl CoreCognitiveEngine {
    pub fn new(dimension: usize) -> Self {
        let base_path = "Personalisasi/Database/Memory_World".to_string();
        fs::create_dir_all(format!("{}/Episodic_Log", base_path)).unwrap();
        fs::create_dir_all(format!("{}/Semantic_Knowledge", base_path)).unwrap();
        fs::create_dir_all(format!("{}/Alliance_Matrix", base_path)).unwrap();

        Self {
            dimension,
            lattice_quantizer: binary_lattice::BinaryLatticeQuantizer::new(dimension),
            gated_router: dynamic_hnsw_router::DynamicHnswRouter::new(dimension),
            residual_guard: residual_cache::ResidualCacheBuffer::new(dimension),
            epistemic_graph: epistemic_graph::EpistemicWorldGraph::new(),
            persistence_guard: persistence_store::PersistenceStoreManager::new(),
            tool_binder: tool_binder::CoreEnvironmentToolBinder::new(),
            tool_executor: tool_executor::CoreEnvironmentToolExecutor::new(),
            state_machine: state_machine::DeterministicCognitiveStateMachine::new(), // INISIALISASI FSM
            database_vault: std::sync::Mutex::new(Vec::new()),
            mandated_path: base_path,
        }
    }

    pub fn serialize_to_mandated_disk(&self, event: &CognitiveEvent) -> Result<(), String> {
        let sub_folder = match event.event_type.as_str() {
            "EPISODIC" => "Episodic_Log",
            "SEMANTIC" => "Semantic_Knowledge",
            "ALLIANCE" => "Alliance_Matrix",
            _ => "Episodic_Log", 
        };

        let file_path = format!("{}/{}/{}.json", self.mandated_path, sub_folder, event.event_id);
        let json_data = format!(
            "{{\"event_id\":\"{}\",\"event_type\":\"{}\",\"payload\":{},\"timestamp\":{},\"ttl\":{}}}",
            event.event_id, event.event_type, event.context_payload, event.timestamp, event.ttl_seconds
        );

        let mut file = File::create(&file_path)
            .map_err(|e| format!("Path Lock Violation Storage Error: {}", e))?;
        file.write_all(json_data.as_bytes())
            .map_err(|e| format!("Disk Write Failure: {}", e))?;
        Ok(())
    }

    pub fn query_with_dynamic_gating(
        &self,
        query_vector: &[f32],
        gate_mode: EmotionalGateMode,
        top_k: usize,
        absolute_floor: f32,
        current_recursive_pass: u8,
    ) -> Result<Vec<(String, f32, String)>, String> {
        let local_vault_snapshot = {
            let guard = self.database_vault.lock().map_err(|e| e.to_string())?;
            guard.clone()
        };

        let mut scored_results: Vec<(String, f32, String)> = Vec::new();
        let mut expert_weights = Vec::with_capacity(local_vault_snapshot.len());
        let mut expert_classes = Vec::with_capacity(local_vault_snapshot.len());

        let packed_query = self.lattice_quantizer.execute_lattice_compression(query_vector)?;

        for event in local_vault_snapshot.iter() {
            let packed_event = self.lattice_quantizer.execute_lattice_compression(&event.embedding)?;
            
            if let Ok(raw_score) = self.lattice_quantizer.compute_bitwise_hamming_distance(&packed_event, &packed_query) {
                
                let compensated_score = self.residual_guard.apply_residual_compensation(&event.event_id, raw_score);

                let applied_score = match (gate_mode, event.event_type.as_str()) {
                    (EmotionalGateMode::DefensiveHostile, "EPISODIC") => (compensated_score + 0.25).min(1.0),
                    (EmotionalGateMode::HyperFocused, "SEMANTIC") => (compensated_score + 0.40).min(1.0),
                    (EmotionalGateMode::SuppressedCompassion, "ALLIANCE") => (compensated_score + 0.15).min(1.0),
                    _ => compensated_score,
                };

                if applied_score >= absolute_floor {
                    scored_results.push((event.event_id.clone(), applied_score, event.context_payload.clone()));
                    expert_weights.push(applied_score);
                    expert_classes.push(event.event_type.clone());
                }
            }
        }

        if !expert_weights.is_empty() {
            self.gated_router.compute_softmax_probabilities(&mut expert_weights, &expert_classes);
            for (idx, result) in scored_results.iter_mut().enumerate() {
                if idx < expert_weights.len() {
                    result.1 = self.gated_router.balance_expert_routing_score(result.1, expert_weights[idx]);
                    self.gated_router.track_expert_invocation(&expert_classes[idx]);
                }
            }
        }

        if scored_results.is_empty() && current_recursive_pass >= 3 {
            return Err("SYSTEM_REACHED_ABSOLUTE_LOGICAL_BOUNDARY".to_string());
        }

        scored_results.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));
        scored_results.truncate(top_k.min(self.gated_router.expert_capacity_limit));

        Ok(scored_results)
    }
}

pub mod mod_engine {
    pub use crate::vector_engine::{CognitiveEvent, EmotionalGateMode, CoreCognitiveEngine};
}

pub mod metabolism_bridge {
    pub use crate::metabolism::MetabolismEngine;
}


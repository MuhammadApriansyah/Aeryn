use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;
use std::sync::Arc;
use tokio::sync::RwLock;
use std::time::{SystemTime, UNIX_EPOCH};

pub mod vector_engine;
pub mod metabolism;

use crate::vector_engine::mod_engine as core_engine;
use crate::vector_engine::mod_engine::{CoreCognitiveEngine, EmotionalGateMode};
use crate::vector_engine::state_machine::CognitiveState;
use crate::metabolism::MetabolismEngine;

#[pyclass]
pub struct PyUnifiedCognitiveSystem {
    pub vector_engine: Arc<CoreCognitiveEngine>,
    pub metabolism_engine: Arc<RwLock<MetabolismEngine>>,
}

#[pymethods]
impl PyUnifiedCognitiveSystem {
    #[new]
    pub fn new(dimension: usize, idle_threshold: u64) -> Self {
        Self {
            vector_engine: Arc::new(CoreCognitiveEngine::new(dimension)),
            metabolism_engine: Arc::new(RwLock::new(MetabolismEngine::new(idle_threshold))),
        }
    }

    pub fn inject_cognitive_event(
        &self,
        event_id: String,
        event_type: String,
        embedding: Vec<f32>,
        context_payload: String,
        ttl_seconds: u64,
    ) -> PyResult<()> {
        let event = core_engine::CognitiveEvent {
            event_id,
            event_type,
            embedding,
            context_payload,
            timestamp: SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs(),
            ttl_seconds,
        };

        if let Ok(mut vault) = self.vector_engine.database_vault.lock() {
            vault.push(event.clone());
        }

        let _ = self.vector_engine.serialize_to_mandated_disk(&event);
        Ok(())
    }

    pub fn route_stimulus_with_gating(
        &self,
        _py: Python<'_>,
        stimulus_vector: Vec<f32>,
        gate_mode_code: u8,
        absolute_floor: f32,
        current_recursive_pass: u8,
    ) -> PyResult<Vec<(String, f32, String)>> {
        let engine = Arc::clone(&self.vector_engine);
        let metabolism = Arc::clone(&self.metabolism_engine);
        let input_len = stimulus_vector.len();

        _py.allow_threads(move || {
            let rt = tokio::runtime::Runtime::new().unwrap();
            let _ = rt.block_on(async {
                let mut metab_write = metabolism.write().await;
                metab_write.execute_metabolic_tick(input_len)
            });

            let gate_mode = match gate_mode_code {
                0 => core_engine::EmotionalGateMode::DefensiveHostile,
                1 => core_engine::EmotionalGateMode::HyperFocused,
                2 => core_engine::EmotionalGateMode::SuppressedCompassion,
                _ => core_engine::EmotionalGateMode::BalancedDefault,
            };

            engine.query_with_dynamic_gating(&stimulus_vector, gate_mode, 5, absolute_floor, current_recursive_pass)
                .map_err(|e| PyValueError::new_err(e))
        })
    }

    pub fn save_affective_checkpoint(&self, session_id: String, pragmatism: f32, hostility: f32, focus: f32, compassionate: f32) -> PyResult<()> {
        self.vector_engine.persistence_guard
            .save_affective_tensor_checkpoint_isolated(&session_id, pragmatism, hostility, focus, compassionate)
            .map_err(|e| PyValueError::new_err(format!("FFI Multi-Session Save Error: {}", e)))?;
        Ok(())
    }

    pub fn load_affective_checkpoint(&self, session_id: String) -> PyResult<Option<(f32, f32, f32, f32)>> {
        let state = self.vector_engine.persistence_guard
            .load_affective_tensor_checkpoint_isolated(&session_id);
        Ok(state)
    }

    pub fn traverse_associated_neighbors(&self, session_id: String, start_node_id: String) -> PyResult<Vec<(String, String, f32)>> {
        let neighbors = self.vector_engine.epistemic_graph
            .traverse_associated_neighbors_isolated(&session_id, &start_node_id);
        Ok(neighbors)
    }

    pub fn upsert_memory_node(&self, session_id: String, id: String, class: String) -> PyResult<()> {
        self.vector_engine.epistemic_graph
            .upsert_memory_node_isolated(&session_id, &id, &class)
            .map_err(|e| PyValueError::new_err(e))?;
        Ok(())
    }

    pub fn connect_semantic_edge(&self, session_id: String, source_id: String, target_id: String, relation: String, weight: f32) -> PyResult<()> {
        self.vector_engine.epistemic_graph
            .connect_semantic_edge_isolated(&session_id, &source_id, &target_id, &relation, weight)
            .map_err(|e| PyValueError::new_err(e))?;
        Ok(())
    }

    pub fn bind_environment_tool(&self, session_id: String, tool_name: String, description: String, json_schema_parameters: String, clearance_level: u8) -> PyResult<()> {
        self.vector_engine.tool_binder
            .bind_external_environment_tool(&session_id, &tool_name, &description, &json_schema_parameters, clearance_level)
            .map_err(|e| PyValueError::new_err(e))?;
        Ok(())
    }

    pub fn compile_tools_manifest(&self, session_id: String) -> PyResult<String> {
        let manifest = self.vector_engine.tool_binder.compile_available_tools_manifest(&session_id);
        Ok(manifest)
    }

    pub fn trigger_read_environment_file_call(&self, target_path: String) -> PyResult<String> {
        let result = self.vector_engine.tool_executor
            .execute_read_tactical_environment_file(&target_path)
            .map_err(|e| PyValueError::new_err(e))?;
        Ok(result)
    }

    pub fn trigger_hardware_clock_telemetry_call(&self) -> PyResult<String> {
        let result = self.vector_engine.tool_executor
            .execute_fetch_hardware_epoch_telemetry()
            .map_err(|e| PyValueError::new_err(e))?;
        Ok(result)
    }

    // =====================================================================
    // UPGRADE COGOS V17 FFI CONTROL: Ekspos fungsi FSM State Machine ke Python layer
    // =====================================================================
    pub fn read_active_state_token(&self) -> PyResult<String> {
        Ok(self.vector_engine.state_machine.get_current_state_string())
    }

    pub fn enforce_state_transition(&self, gate_code: u8) -> PyResult<()> {
        let target_state = match gate_code {
            0 => CognitiveState::Idle,
            1 => CognitiveState::AffectiveCompute,
            2 => CognitiveState::NeuroSymbolicSearch,
            3 => CognitiveState::LlmInferenceLock,
            4 => CognitiveState::ObservationIntercept,
            _ => CognitiveState::Idle,
        };

        self.vector_engine.state_machine
            .request_state_transition(target_state)
            .map_err(|e| PyValueError::new_err(e))?;
        Ok(())
    }
    // =====================================================================

    pub fn trigger_digital_dreaming(&self, _py: Python<'_>) -> PyResult<usize> {
        let engine = Arc::clone(&self.vector_engine);
        let metabolism = Arc::clone(&self.metabolism_engine);
        let current_time = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs();

        _py.allow_threads(move || {
            let rt = tokio::runtime::Runtime::new().unwrap();
            rt.block_on(async {
                let mut metab_write = metabolism.write().await;
                metab_write.execute_digital_dreaming_consolidation(&engine, current_time).await
                    .map_err(|e| PyValueError::new_err(e))
            })
        })
    }
}

#[pyclass]
pub struct CharacterProgression;
#[pymethods]
impl CharacterProgression { #[new] fn new() -> Self { Self } }

#[pyclass]
pub struct MagicSystemEngine;
#[pymethods]
impl MagicSystemEngine { #[new] fn new() -> Self { Self } }

#[pyclass]
pub struct TransactionEntry;
#[pymethods]
impl TransactionEntry { #[new] fn new() -> Self { Self } }

#[pyclass]
pub struct AccountingLedgerEngine;
#[pymethods]
impl AccountingLedgerEngine { #[new] fn new() -> Self { Self } }

#[pymodule]
fn aeryn_native(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_class::<PyUnifiedCognitiveSystem>()?;
    m.add_class::<CharacterProgression>()?;
    m.add_class::<MagicSystemEngine>()?;
    m.add_class::<TransactionEntry>()?;
    m.add_class::<AccountingLedgerEngine>()?;
    Ok(())
}


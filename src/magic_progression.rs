use std::collections::HashMap;
use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;

#[pyclass]
#[derive(Debug, Clone)]
pub struct CharacterProgression {
    #[pyo3(get, set)]
    pub id: String,
    #[pyo3(get, set)]
    pub current_level: u32,
    #[pyo3(get, set)]
    pub experience_points: u64,
    #[pyo3(get, set)]
    pub akue_energy_pool: f32,
    #[pyo3(get, set)]
    pub max_energy_capacity: f32,
    pub active_modifiers: HashMap<String, f32>,
}

#[pymethods]
impl CharacterProgression {
    #[new]
    pub fn new(id: String, current_level: u32, experience_points: u64, akue_energy_pool: f32, max_energy: f32) -> Self {
        Self {
            id,
            current_level,
            experience_points,
            akue_energy_pool,
            max_energy_capacity: max_energy,
            active_modifiers: HashMap::new(),
        }
    }
}

#[pyclass]
pub struct MagicSystemEngine {
    #[pyo3(get, set)]
    pub base_entropy_coefficient: f32,
    #[pyo3(get, set)]
    pub base_utility_coefficient: f32,
}

#[pymethods]
impl MagicSystemEngine {
    #[new]
    pub fn new(entropy_coef: f32, utility_coef: f32) -> Self {
        Self { 
            base_entropy_coefficient: entropy_coef,
            base_utility_coefficient: utility_coef,
        }
    }

    pub fn evaluate_akue_spell_cast(
        &self, 
        character: &mut CharacterProgression, 
        activation_cost: f32, 
        kinetic_multiplier: f32,
        utility_complexity_tier: u32,
        spell_name: &str
    ) -> PyResult<(f32, f32, f32, String)> {
        
        if activation_cost <= 0.0 || kinetic_multiplier <= 0.0 {
            return Err(PyValueError::new_err("AKUE Core Exception: Costs and multipliers must be positive."));
        }

        let efficiency_modifier = character.active_modifiers.get("mana_efficiency").unwrap_or(&1.0);
        let kinetic_buff = character.active_modifiers.get("kinetic_boost").unwrap_or(&1.0);

        let real_activation_drain = activation_cost * efficiency_modifier;
        let real_kinetic_output = real_activation_drain * kinetic_multiplier * kinetic_buff;
        let utility_cost = (utility_complexity_tier as f32) * self.base_utility_coefficient;
        let entropy_cost = real_activation_drain * self.base_entropy_coefficient;

        let total_akue_drain = real_activation_drain + utility_cost + entropy_cost;

        if character.akue_energy_pool < total_akue_drain {
            return Err(PyValueError::new_err(format!(
                "AKUE Energy Pool Insufficient. Required: {:.4}, Available: {:.4}.",
                total_akue_drain, character.akue_energy_pool
            )));
        }

        character.akue_energy_pool -= total_akue_drain;

        let vector_context_payload = format!(
            "{{\"event_class\":\"SPELL_CAST\",\"character_id\":\"{}\",\"spell\":\"{}\",\"kinetic_output\":{:.4},\"entropy_damage\":{:.4},\"remaining_pool\":{:.4}}}",
            character.id, spell_name, real_kinetic_output, entropy_cost, character.akue_energy_pool
        );
        
        Ok((real_kinetic_output, entropy_cost, character.akue_energy_pool, vector_context_payload))
    }

    pub fn apply_experience_gain(&self, character: &mut CharacterProgression, exp: u64) -> (bool, String) {
        character.experience_points += exp;
        let next_level_threshold = (character.current_level as u64) * 1500;
        let mut level_up_triggered = false;
        
        if character.experience_points >= next_level_threshold {
            character.current_level += 1;
            character.max_energy_capacity += 100.0;
            character.akue_energy_pool = character.max_energy_capacity;
            level_up_triggered = true;
        }

        let progression_payload = format!(
            "{{\"event_class\":\"PROGRESSION_UPDATE\",\"character_id\":\"{}\",\"current_level\":{},\"total_xp\":{},\"level_up\":{}}}",
            character.id, character.current_level, character.experience_points, level_up_triggered
        );

        (level_up_triggered, progression_payload)
    }
}


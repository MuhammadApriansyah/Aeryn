use std::sync::Mutex;

#[derive(Clone, Copy, Debug, PartialEq)]
pub enum CognitiveState {
    Idle,
    AffectiveCompute,
    NeuroSymbolicSearch,
    LlmInferenceLock,
    ObservationIntercept,
}

pub struct DeterministicCognitiveStateMachine {
    current_state: Mutex<CognitiveState>,
}

impl DeterministicCognitiveStateMachine {
    pub fn new() -> Self {
        Self {
            current_state: Mutex::new(CognitiveState::Idle),
        }
    }

    pub fn get_current_state_string(&self) -> String {
        let guard = self.current_state.lock().unwrap();
        format!("{:?}", *guard).to_uppercase()
    }

    pub fn request_state_transition(&self, next_state: CognitiveState) -> Result<(), String> {
        let mut guard = self.current_state.lock().unwrap();
        let current = *guard;

        let is_valid_transition = match (current, next_state) {
            (CognitiveState::Idle, CognitiveState::AffectiveCompute) => true,
            (CognitiveState::AffectiveCompute, CognitiveState::NeuroSymbolicSearch) => true,
            (CognitiveState::NeuroSymbolicSearch, CognitiveState::LlmInferenceLock) => true,
            (CognitiveState::LlmInferenceLock, CognitiveState::ObservationIntercept) => true,
            (CognitiveState::ObservationIntercept, CognitiveState::Idle) => true,
            (_, CognitiveState::Idle) => true,
            _ => false,
        };

        if is_valid_transition {
            *guard = next_state;
            Ok(())
        } else {
            Err(format!(
                "Architectural Constraint Violation: Illegal cognitive state transition requested from {:?} to {:?}",
                current, next_state
            ))
        }
    }
}


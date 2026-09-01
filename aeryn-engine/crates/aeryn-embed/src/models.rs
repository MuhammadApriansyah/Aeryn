use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ModelInfo {
    pub name: String,
    pub model_type: ModelType,
    pub dimensions: usize,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ModelType {
    OpenAi,
    HuggingFace,
    Local,
}

pub struct ModelRegistry;

impl ModelRegistry {
    pub fn new() -> Self {
        Self
    }
}

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BatchConfig {
    pub batch_size: usize,
    pub max_retries: u32,
}

impl Default for BatchConfig {
    fn default() -> Self {
        Self {
            batch_size: 100,
            max_retries: 3,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BatchResult {
    pub success_count: usize,
    pub failure_count: usize,
}

pub struct BatchEmbedder;

impl BatchEmbedder {
    pub fn new() -> Self {
        Self
    }
}

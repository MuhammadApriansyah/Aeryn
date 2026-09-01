//! Embedding engine module.

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EmbeddingConfig {
    pub model: String,
    pub dimensions: usize,
    pub batch_size: usize,
}

impl Default for EmbeddingConfig {
    fn default() -> Self {
        Self {
            model: "text-embedding-3-small".to_string(),
            dimensions: 1536,
            batch_size: 100,
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum EmbeddingModel {
    OpenAiSmall,
    OpenAiLarge,
    HuggingFace,
    Local,
}

pub struct EmbeddingEngine;

impl EmbeddingEngine {
    pub fn new(config: EmbeddingConfig) -> Self {
        Self
    }

    pub fn embed(&self, _text: &str) -> Vec<f32> {
        vec![0.0; 1536]
    }

    pub fn embed_batch(&self, texts: &[&str]) -> Vec<Vec<f32>> {
        texts.iter().map(|_| vec![0.0; 1536]).collect()
    }
}

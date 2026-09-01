pub mod embedder;
pub mod models;
pub mod batch;

pub use embedder::{EmbeddingEngine, EmbeddingConfig, EmbeddingModel};
pub use models::{ModelRegistry, ModelInfo, ModelType};
pub use batch::{BatchEmbedder, BatchConfig, BatchResult};

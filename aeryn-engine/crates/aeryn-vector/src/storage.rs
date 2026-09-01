use std::path::Path;

use serde::{Deserialize, Serialize};
use tracing::{debug, instrument};

use aeryn_core::error::{AerynError, AerynResult};
use aeryn_core::types::Id;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum StorageFormat {
    Bincode,
    Json,
}

impl Default for StorageFormat {
    fn default() -> Self {
        StorageFormat::Bincode
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StorageConfig {
    pub path: String,
    pub format: StorageFormat,
}

impl Default for StorageConfig {
    fn default() -> Self {
        Self {
            path: "./vector_store".to_string(),
            format: StorageFormat::Bincode,
        }
    }
}

#[derive(Debug)]
pub struct VectorStorage {
    config: StorageConfig,
}

impl VectorStorage {
    pub fn new(config: StorageConfig) -> Self {
        Self { config }
    }

    pub fn with_default_config() -> Self {
        Self::new(StorageConfig::default())
    }

    #[instrument(skip(self, vector))]
    pub fn persist_vector(&self, id: &Id, vector: &[f32]) -> AerynResult<()> {
        let path = Path::new(&self.config.path);
        std::fs::create_dir_all(path)?;

        let file_name = format!("{}.bin", id);
        let file_path = path.join(&file_name);

        let data = bincode::serialize(vector)
            .map_err(|e| AerynError::Serialization(e.to_string()))?;

        std::fs::write(&file_path, &data)?;
        debug!("Persisted vector {} ({} bytes)", id, data.len());

        Ok(())
    }

    pub fn load_vector(&self, id: &Id) -> AerynResult<Vec<f32>> {
        let path = Path::new(&self.config.path);
        let file_name = format!("{}.bin", id);
        let file_path = path.join(&file_name);

        let data = std::fs::read(&file_path)?;
        let vector = bincode::deserialize(&data)
            .map_err(|e| AerynError::Deserialization(e.to_string()))?;

        Ok(vector)
    }

    pub fn delete_vector(&self, id: &Id) -> AerynResult<()> {
        let path = Path::new(&self.config.path);
        let file_name = format!("{}.bin", id);
        let file_path = path.join(&file_name);

        if file_path.exists() {
            std::fs::remove_file(&file_path)?;
        }

        Ok(())
    }

    pub fn get_config(&self) -> &StorageConfig {
        &self.config
    }
}

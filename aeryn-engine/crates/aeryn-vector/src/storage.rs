//! Persistence layer for vector storage.

use std::collections::HashMap;
use std::path::Path;

use serde::{Deserialize, Serialize};
use tracing::{debug, info, instrument};

use aeryn_core::error::{AerynError, AerynResult};
use aeryn_core::types::Id;

/// Storage format options.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum StorageFormat {
    /// Binary format using bincode.
    Bincode,
    /// JSON format (larger but human-readable).
    Json,
    /// Compressed binary format.
    Compressed,
}

impl Default for StorageFormat {
    fn default() -> Self {
        StorageFormat::Bincode
    }
}

/// Configuration for vector storage.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StorageConfig {
    /// Path to the storage directory.
    pub path: String,
    /// Storage format.
    pub format: StorageFormat,
    /// Whether to compress data.
    pub compress: bool,
    /// Maximum file size in bytes.
    pub max_file_size: u64,
    /// Whether to use memory-mapped files.
    pub mmap: bool,
}

impl Default for StorageConfig {
    fn default() -> Self {
        Self {
            path: "./vector_store".to_string(),
            format: StorageFormat::Bincode,
            compress: false,
            max_file_size: 1024 * 1024 * 1024, // 1GB
            mmap: true,
        }
    }
}

/// Vector storage for persistence.
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

    pub fn list_vectors(&self) -> AerynResult<Vec<Id>> {
        let path = Path::new(&self.config.path);
        let mut ids = Vec::new();

        if path.exists() {
            for entry in std::fs::read_dir(path)? {
                let entry = entry?;
                let path = entry.path();
                if path.extension().and_then(|e| e.to_str()) == Some("bin") {
                    if let Some(stem) = path.file_stem().and_then(|s| s.to_str()) {
                        if let Ok(id) = Self::parse_id(stem) {
                            ids.push(id);
                        }
                    }
                }
            }
        }

        Ok(ids)
    }

    fn parse_id(s: &str) -> AerynResult<Id> {
        let bytes = hex::decode(s)
            .map_err(|e| AerynError::InvalidInput(e.to_string()))?;
        if bytes.len() != 16 {
            return Err(AerynError::InvalidInput("Invalid ID length".to_string()));
        }
        let mut arr = [0u8; 16];
        arr.copy_from_slice(&bytes);
        Ok(Id(arr))
    }

    pub fn get_config(&self) -> &StorageConfig {
        &self.config
    }
}

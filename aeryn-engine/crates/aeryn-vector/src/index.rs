use std::collections::HashMap;
use std::sync::Arc;

use parking_lot::RwLock;
use serde::{Deserialize, Serialize};
use tracing::{debug, instrument};

use aeryn_core::error::{AerynError, AerynResult};
use aeryn_core::types::Id;

use crate::distance::DistanceMetric;
use crate::storage::{StorageConfig, StorageFormat, VectorStorage};

#[derive(Debug, Clone)]
pub struct VectorSearchOptions {
    pub k: usize,
    pub filters: HashMap<String, String>,
    pub include_vectors: bool,
    pub include_metadata: bool,
    pub min_score: Option<f32>,
}

impl Default for VectorSearchOptions {
    fn default() -> Self {
        Self {
            k: 10,
            filters: HashMap::new(),
            include_vectors: false,
            include_metadata: true,
            min_score: None,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VectorSearchResult {
    pub id: Id,
    pub score: f32,
    pub vector: Option<Vec<f32>>,
    pub metadata: Option<HashMap<String, String>>,
}

impl VectorSearchResult {
    pub fn new(id: Id, score: f32) -> Self {
        Self {
            id,
            score,
            vector: None,
            metadata: None,
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum IndexType {
    BruteForce,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VectorIndexConfig {
    pub index_type: IndexType,
    pub dimensions: usize,
    pub metric: DistanceMetric,
    pub storage: Option<StorageConfig>,
}

impl Default for VectorIndexConfig {
    fn default() -> Self {
        Self {
            index_type: IndexType::BruteForce,
            dimensions: 1536,
            metric: DistanceMetric::Cosine,
            storage: None,
        }
    }
}

pub struct VectorIndex {
    config: VectorIndexConfig,
    vectors: RwLock<HashMap<Id, Vec<f32>>>,
    metadata: RwLock<HashMap<Id, HashMap<String, String>>>,
    storage: Option<VectorStorage>,
}

impl VectorIndex {
    pub fn new(config: VectorIndexConfig) -> AerynResult<Self> {
        let storage = if config.storage.is_some() {
            Some(VectorStorage::new(config.storage.clone().unwrap()))
        } else {
            None
        };

        Ok(Self {
            config,
            vectors: RwLock::new(HashMap::new()),
            metadata: RwLock::new(HashMap::new()),
            storage,
        })
    }

    pub fn with_default_config(dimensions: usize) -> AerynResult<Self> {
        Self::new(VectorIndexConfig {
            dimensions,
            ..Default::default()
        })
    }

    pub fn config(&self) -> &VectorIndexConfig {
        &self.config
    }

    pub fn len(&self) -> usize {
        self.vectors.read().len()
    }

    pub fn is_empty(&self) -> bool {
        self.vectors.read().is_empty()
    }

    #[instrument(skip(self, vector))]
    pub fn insert(&self, id: Id, vector: Vec<f32>, metadata: Option<HashMap<String, String>>) -> AerynResult<()> {
        if !vector.is_empty() && vector.len() != self.config.dimensions {
            return Err(AerynError::Validation(format!(
                "Vector dimension mismatch: expected {}, got {}",
                self.config.dimensions,
                vector.len()
            )));
        }

        self.vectors.write().insert(id, vector.clone());

        if let Some(meta) = metadata {
            self.metadata.write().insert(id, meta);
        }

        if let Some(ref storage) = self.storage {
            storage.persist_vector(&id, &vector)?;
        }

        debug!("Inserted vector {} (total: {})", id, self.len());
        Ok(())
    }

    pub fn batch_insert(&self, items: Vec<(Id, Vec<f32>, Option<HashMap<String, String>>)>) -> AerynResult<()> {
        for (id, vector, metadata) in items {
            self.insert(id, vector, metadata)?;
        }
        Ok(())
    }

    pub fn search(&self, query: &[f32], options: VectorSearchOptions) -> AerynResult<Vec<VectorSearchResult>> {
        if query.len() != self.config.dimensions {
            return Err(AerynError::Validation(format!(
                "Query dimension mismatch: expected {}, got {}",
                self.config.dimensions,
                query.len()
            )));
        }

        let vectors = self.vectors.read();
        let meta = self.metadata.read();

        let mut results: Vec<VectorSearchResult> = Vec::new();

        for (id, vector) in vectors.iter() {
            let distance = crate::distance::compute_distance(self.config.metric, query, vector);
            
            let score = if self.config.metric == DistanceMetric::Cosine {
                1.0 - distance
            } else {
                1.0 / (1.0 + distance)
            };

            if let Some(min) = options.min_score {
                if score < min {
                    continue;
                }
            }

            let metadata = meta.get(id);
            
            if !options.filters.is_empty() {
                if let Some(m) = metadata {
                    let matches = options.filters.iter().all(|(k, v)| {
                        m.get(k).map(|val| val == v).unwrap_or(false)
                    });
                    if !matches {
                        continue;
                    }
                } else {
                    continue;
                }
            }

            let mut result = VectorSearchResult::new(*id, score);

            if options.include_vectors {
                result.vector = Some(vector.clone());
            }

            if options.include_metadata {
                result.metadata = metadata.cloned();
            }

            results.push(result);
        }

        results.sort_by(|a, b| b.score.partial_cmp(&a.score).unwrap_or(std::cmp::Ordering::Equal));
        results.truncate(options.k);

        Ok(results)
    }

    pub fn remove(&self, id: &Id) -> AerynResult<()> {
        self.vectors.write().remove(id);
        self.metadata.write().remove(id);
        Ok(())
    }

    pub fn get_metadata(&self, id: &Id) -> Option<HashMap<String, String>> {
        self.metadata.read().get(id).cloned()
    }

    pub fn set_metadata(&self, id: Id, metadata: HashMap<String, String>) -> AerynResult<()> {
        if !self.vectors.read().contains_key(&id) {
            return Err(AerynError::NotFound(format!("Vector {} not found", id)));
        }
        self.metadata.write().insert(id, metadata);
        Ok(())
    }

    pub fn contains(&self, id: &Id) -> bool {
        self.vectors.read().contains_key(id)
    }

    pub fn dimensions(&self) -> usize {
        self.config.dimensions
    }

    pub fn clear(&self) {
        self.vectors.write().clear();
        self.metadata.write().clear();
    }
}

impl std::fmt::Debug for VectorIndex {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("VectorIndex")
            .field("config", &self.config)
            .field("len", &self.len())
            .finish()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_insert_and_search() -> AerynResult<()> {
        let index = VectorIndex::with_default_config(3)?;
        
        let id1 = Id::new();
        let id2 = Id::new();
        
        index.insert(id1, vec![1.0, 0.0, 0.0], None)?;
        index.insert(id2, vec![0.0, 1.0, 0.0], None)?;
        
        let results = index.search(&[1.0, 0.0, 0.0], VectorSearchOptions::default())?;
        
        assert_eq!(results.len(), 2);
        assert_eq!(results[0].id, id1);
        assert!(results[0].score > results[1].score);
        
        Ok(())
    }

    #[test]
    fn test_remove() -> AerynResult<()> {
        let index = VectorIndex::with_default_config(2)?;
        let id = Id::new();
        
        index.insert(id, vec![1.0, 2.0], None)?;
        assert_eq!(index.len(), 1);
        
        index.remove(&id)?;
        assert_eq!(index.len(), 0);
        
        Ok(())
    }

    #[test]
    fn test_metadata() -> AerynResult<()> {
        let index = VectorIndex::with_default_config(2)?;
        let id = Id::new();
        
        let mut meta = HashMap::new();
        meta.insert("key".to_string(), "value".to_string());
        
        index.insert(id, vec![1.0, 2.0], Some(meta.clone()))?;
        
        let retrieved = index.get_metadata(&id);
        assert!(retrieved.is_some());
        assert_eq!(retrieved.unwrap().get("key").unwrap(), "value");
        
        Ok(())
    }
}

//! Vector index abstraction layer.
//!
//! Provides a unified interface for different vector index implementations:
//! - HNSW (Hierarchical Navigable Small World) for approximate search
//! - Brute force for exact search
//! - Hybrid for combined approaches

use std::sync::Arc;

use hashbrown::HashMap;
use parking_lot::RwLock;
use serde::{Deserialize, Serialize};
use tracing::{debug, info, instrument};

use aeryn_core::error::{AerynError, AerynResult};
use aeryn_core::types::Id;

use crate::distance::DistanceMetric;
use crate::hnsw::{HnswConfig, HnswIndex};
use crate::storage::{StorageConfig, StorageFormat, VectorStorage};

/// Vector search options.
#[derive(Debug, Clone)]
pub struct VectorSearchOptions {
    /// Number of results to return.
    pub k: usize,
    /// Filter by metadata key-value pairs.
    pub filters: HashMap<String, String>,
    /// Whether to include the vector data in results.
    pub include_vectors: bool,
    /// Whether to include metadata in results.
    pub include_metadata: bool,
    /// Minimum similarity score threshold.
    pub min_score: Option<f32>,
    /// Search ef_override.
    pub ef_search: Option<usize>,
}

impl Default for VectorSearchOptions {
    fn default() -> Self {
        Self {
            k: 10,
            filters: HashMap::new(),
            include_vectors: false,
            include_metadata: true,
            min_score: None,
            ef_search: None,
        }
    }
}

/// A single vector search result.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VectorSearchResult {
    /// The vector ID.
    pub id: Id,
    /// The distance/similarity score.
    pub score: f32,
    /// The vector data (if requested).
    pub vector: Option<Vec<f32>>,
    /// Metadata (if requested).
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

    pub fn with_vector(mut self, vector: Vec<f32>) -> Self {
        self.vector = Some(vector);
        self
    }

    pub fn with_metadata(mut self, metadata: HashMap<String, String>) -> Self {
        self.metadata = Some(metadata);
        self
    }
}

/// Vector index implementation type.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum IndexType {
    /// HNSW index for approximate nearest neighbor search.
    Hnsw,
    /// Brute force index for exact nearest neighbor search.
    BruteForce,
    /// Hybrid index combining HNSW and brute force.
    Hybrid,
}

impl IndexType {
    pub fn from_str(s: &str) -> Option<Self> {
        match s.to_lowercase().as_str() {
            "hnsw" => Some(IndexType::Hnsw),
            "brute_force" | "bruteforce" | "exact" => Some(IndexType::BruteForce),
            "hybrid" => Some(IndexType::Hybrid),
            _ => None,
        }
    }
}

/// Configuration for the vector index.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VectorIndexConfig {
    /// Type of index to use.
    pub index_type: IndexType,
    /// Dimensionality of vectors.
    pub dimensions: usize,
    /// Distance metric to use.
    pub metric: DistanceMetric,
    /// HNSW-specific configuration.
    pub hnsw: Option<HnswConfig>,
    /// Storage configuration.
    pub storage: Option<StorageConfig>,
    /// Maximum number of vectors.
    pub max_vectors: usize,
    /// Whether to enable WAL (write-ahead logging).
    pub enable_wal: bool,
}

impl Default for VectorIndexConfig {
    fn default() -> Self {
        Self {
            index_type: IndexType::Hnsw,
            dimensions: 1536,
            metric: DistanceMetric::Cosine,
            hnsw: None,
            storage: None,
            max_vectors: 1_000_000,
            enable_wal: true,
        }
    }
}

/// Vector index — the main entry point for vector operations.
pub struct VectorIndex {
    config: VectorIndexConfig,
    hnsw: Option<HnswIndex>,
    brute_force: Option<BruteForceIndex>,
    storage: Option<VectorStorage>,
    metadata: RwLock<HashMap<Id, HashMap<String, String>>>,
}

impl VectorIndex {
    /// Create a new vector index with the given configuration.
    pub fn new(config: VectorIndexConfig) -> AerynResult<Self> {
        let hnsw = if config.index_type == IndexType::Hnsw || config.index_type == IndexType::Hybrid {
            let hnsw_config = config.hnsw.clone().unwrap_or_default();
            Some(HnswIndex::new(hnsw_config))
        } else {
            None
        };

        let brute_force = if config.index_type == IndexType::BruteForce || config.index_type == IndexType::Hybrid {
            Some(BruteForceIndex::new(config.metric))
        } else {
            None
        };

        let storage = if config.storage.is_some() {
            Some(VectorStorage::new(config.storage.clone().unwrap()))
        } else {
            None
        };

        Ok(Self {
            config,
            hnsw,
            brute_force,
            storage,
            metadata: RwLock::new(HashMap::new()),
        })
    }

    /// Create a new vector index with default configuration.
    pub fn with_default_config(dimensions: usize) -> AerynResult<Self> {
        let config = VectorIndexConfig {
            dimensions,
            ..Default::default()
        };
        Self::new(config)
    }

    /// Get the configuration.
    pub fn config(&self) -> &VectorIndexConfig {
        &self.config
    }

    /// Get the number of vectors in the index.
    pub fn len(&self) -> usize {
        match self.config.index_type {
            IndexType::Hnsw => self.hnsw.as_ref().map(|h| h.len()).unwrap_or(0),
            IndexType::BruteForce => self.brute_force.as_ref().map(|b| b.len()).unwrap_or(0),
            IndexType::Hybrid => self.hnsw.as_ref().map(|h| h.len()).unwrap_or(0),
        }
    }

    /// Check if the index is empty.
    pub fn is_empty(&self) -> bool {
        self.len() == 0
    }

    /// Insert a vector with optional metadata.
    #[instrument(skip(self, vector), fields(id = %id))]
    pub fn insert(&self, id: Id, vector: Vec<f32>, metadata: Option<HashMap<String, String>>) -> AerynResult<()> {
        // Validate dimensions
        if !vector.is_empty() && vector.len() != self.config.dimensions {
            return Err(AerynError::Validation(format!(
                "Vector dimension mismatch: expected {}, got {}",
                self.config.dimensions,
                vector.len()
            )));
        }

        // Insert into HNSW if available
        if let Some(ref hnsw) = self.hnsw {
            hnsw.insert(id, vector.clone())?;
        }

        // Insert into brute force if available
        if let Some(ref bf) = self.brute_force {
            bf.insert(id, vector.clone());
        }

        // Store metadata
        if let Some(meta) = metadata {
            self.metadata.write().insert(id, meta);
        }

        // Persist to storage if available
        if let Some(ref storage) = self.storage {
            storage.persist_vector(&id, &vector)?;
        }

        debug!("Inserted vector {} (total: {})", id, self.len());
        Ok(())
    }

    /// Batch insert vectors.
    pub fn batch_insert(&self, items: Vec<(Id, Vec<f32>, Option<HashMap<String, String>>)>) -> AerynResult<()> {
        for (id, vector, metadata) in items {
            self.insert(id, vector, metadata)?;
        }
        Ok(())
    }

    /// Search for the k nearest neighbors of a query vector.
    #[instrument(skip(self, query), fields(k = options.k))]
    pub fn search(&self, query: &[f32], options: VectorSearchOptions) -> AerynResult<Vec<VectorSearchResult>> {
        // Validate dimensions
        if query.len() != self.config.dimensions {
            return Err(AerynError::Validation(format!(
                "Query dimension mismatch: expected {}, got {}",
                self.config.dimensions,
                query.len()
            )));
        }

        // Search using the primary index
        let results = match self.config.index_type {
            IndexType::Hnsw => {
                let hnsw = self.hnsw.as_ref().ok_or_else(|| {
                    AerynError::Internal("HNSW index not initialized".to_string())
                })?;
                hnsw.search(query, options.k)?
            }
            IndexType::BruteForce => {
                let bf = self.brute_force.as_ref().ok_or_else(|| {
                    AerynError::Internal("Brute force index not initialized".to_string())
                })?;
                bf.search(query, options.k)?
            }
            IndexType::Hybrid => {
                // Use HNSW first, then refine with brute force if needed
                let hnsw = self.hnsw.as_ref().ok_or_else(|| {
                    AerynError::Internal("HNSW index not initialized".to_string())
                })?;
                hnsw.search(query, options.k)?
            }
        };

        // Convert to VectorSearchResult
        let mut search_results: Vec<VectorSearchResult> = results
            .into_iter()
            .map(|(id, score)| {
                let mut result = VectorSearchResult::new(id, score);
                
                // Add vector data if requested
                if options.include_vectors {
                    if let Some(ref hnsw) = self.hnsw {
                        if let Some(node) = hnsw.get_node(&id) {
                            result = result.with_vector(node.vector);
                        }
                    }
                }
                
                // Add metadata if requested
                if options.include_metadata {
                    let meta = self.metadata.read();
                    if let Some(metadata) = meta.get(&id) {
                        result = result.with_metadata(metadata.clone());
                    }
                }
                
                result
            })
            .collect();

        // Apply minimum score threshold
        if let Some(min_score) = options.min_score {
            search_results.retain(|r| r.score >= min_score);
        }

        // Apply metadata filters
        if !options.filters.is_empty() {
            let meta = self.metadata.read();
            search_results.retain(|r| {
                if let Some(metadata) = meta.get(&r.id) {
                    options.filters.iter().all(|(key, value)| {
                        metadata.get(key).map(|v| v == value).unwrap_or(false)
                    })
                } else {
                    false
                }
            });
        }

        Ok(search_results)
    }

    /// Remove a vector from the index.
    pub fn remove(&self, id: &Id) -> AerynResult<()> {
        // Remove from HNSW
        if let Some(ref hnsw) = self.hnsw {
            hnsw.remove(id)?;
        }

        // Remove from brute force
        if let Some(ref bf) = self.brute_force {
            bf.remove(id);
        }

        // Remove metadata
        self.metadata.write().remove(id);

        Ok(())
    }

    /// Get metadata for a vector.
    pub fn get_metadata(&self, id: &Id) -> Option<HashMap<String, String>> {
        self.metadata.read().get(id).cloned()
    }

    /// Set metadata for a vector.
    pub fn set_metadata(&self, id: &Id, metadata: HashMap<String, String>) -> AerynResult<()> {
        if !self.contains(id) {
            return Err(AerynError::NotFound(format!("Vector {} not found", id)));
        }
        self.metadata.write().insert(*id, metadata);
        Ok(())
    }

    /// Check if a vector exists.
    pub fn contains(&self, id: &Id) -> bool {
        match self.config.index_type {
            IndexType::Hnsw => self.hnsw.as_ref().map(|h| h.contains(id)).unwrap_or(false),
            IndexType::BruteForce => self.brute_force.as_ref().map(|b| b.contains(id)).unwrap_or(false),
            IndexType::Hybrid => self.hnsw.as_ref().map(|h| h.contains(id)).unwrap_or(false),
        }
    }

    /// Get the dimensionality of vectors in the index.
    pub fn dimensions(&self) -> usize {
        self.config.dimensions
    }

    /// Get statistics about the index.
    pub fn stats(&self) -> IndexStats {
        IndexStats {
            vector_count: self.len(),
            dimensions: self.config.dimensions,
            index_type: self.config.index_type,
            metric: self.config.metric,
        }
    }

    /// Clear the index.
    pub fn clear(&self) {
        if let Some(ref hnsw) = self.hnsw {
            hnsw.clear();
        }
        if let Some(ref bf) = self.brute_force {
            bf.clear();
        }
        self.metadata.write().clear();
    }

    /// Rebuild the index.
    pub fn rebuild(&self) -> AerynResult<()> {
        if let Some(ref hnsw) = self.hnsw {
            hnsw.rebuild()?;
        }
        Ok(())
    }
}

/// Statistics about the index.
#[derive(Debug, Clone)]
pub struct IndexStats {
    pub vector_count: usize,
    pub dimensions: usize,
    pub index_type: IndexType,
    pub metric: DistanceMetric,
}

impl std::fmt::Display for IndexStats {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(
            f,
            "IndexStats {{ vectors: {}, dimensions: {}, type: {:?}, metric: {:?} }}",
            self.vector_count, self.dimensions, self.index_type, self.metric
        )
    }
}

/// Brute force vector index for exact nearest neighbor search.
struct BruteForceIndex {
    metric: DistanceMetric,
    vectors: RwLock<HashMap<Id, Vec<f32>>>,
}

impl BruteForceIndex {
    fn new(metric: DistanceMetric) -> Self {
        Self {
            metric,
            vectors: RwLock::new(HashMap::new()),
        }
    }

    fn insert(&self, id: Id, vector: Vec<f32>) {
        self.vectors.write().insert(id, vector);
    }

    fn search(&self, query: &[f32], k: usize) -> AerynResult<Vec<(Id, f32)>> {
        let vectors = self.vectors.read();
        
        let mut results: Vec<(Id, f32)> = vectors
            .iter()
            .map(|(id, vector)| {
                let distance = crate::distance::compute_distance(self.metric, query, vector);
                (*id, distance)
            })
            .collect();
        
        // Sort by distance (ascending)
        results.sort_by(|a, b| a.1.partial_cmp(&b.1).unwrap_or(std::cmp::Ordering::Equal));
        results.truncate(k);
        
        Ok(results)
    }

    fn remove(&self, id: &Id) {
        self.vectors.write().remove(id);
    }

    fn len(&self) -> usize {
        self.vectors.read().len()
    }

    fn contains(&self, id: &Id) -> bool {
        self.vectors.read().contains_key(id)
    }

    fn clear(&self) {
        self.vectors.write().clear();
    }
}

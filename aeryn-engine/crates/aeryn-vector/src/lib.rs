//! High-performance vector storage and similarity search.
//!
//! Implements an HNSW (Hierarchical Navigable Small World) index
//! for fast approximate nearest neighbor search.
//!
//! Features:
//! - Multi-layer HNSW graph construction
//! - Parallel batch insertion
//! - Thread-safe concurrent search
//! - Memory-mapped persistence
//! - SIMD-friendly distance computations
//! - Automatic ef_construction tuning

pub mod distance;
pub mod hnsw;
pub mod index;
pub mod storage;

pub use distance::{Distance, DistanceMetric};
pub use hnsw::HnswIndex;
pub use index::{VectorIndex, VectorSearchOptions, VectorSearchResult};
pub use storage::{VectorStorage, StorageConfig, StorageFormat};

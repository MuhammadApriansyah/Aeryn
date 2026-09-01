use pyo3::prelude::*;
use serde::{Deserialize, Serialize};

#[pyclass]
#[derive(Debug, Clone)]
pub struct PyVectorIndex {
    inner: aeryn_vector::index::VectorIndex,
}

#[pyclass]
#[derive(Debug, Clone)]
pub struct PyVectorSearchResult {
    #[pyo3(get)]
    pub id: String,
    #[pyo3(get)]
    pub score: f32,
    #[pyo3(get)]
    pub vector: Option<Vec<f32>>,
    #[pyo3(get)]
    pub metadata: Option<Vec<(String, String)>>,
}

#[pymethods]
impl PyVectorIndex {
    #[new]
    fn new(dimensions: usize) -> PyResult<Self> {
        let config = aeryn_vector::index::VectorIndexConfig {
            dimensions,
            ..Default::default()
        };
        let inner = aeryn_vector::index::VectorIndex::new(config)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
        Ok(Self { inner })
    }

    fn insert(&self, id: String, vector: Vec<f32>) -> PyResult<()> {
        let id_bytes = hex::decode(&id).map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
        let mut id_arr = [0u8; 16];
        id_arr.copy_from_slice(&id_bytes);
        let id = aeryn_core::types::Id(id_arr);
        
        self.inner.insert(id, vector, None)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))
    }

    fn search(&self, query: Vec<f32>, k: usize) -> PyResult<Vec<PyVectorSearchResult>> {
        let options = aeryn_vector::index::VectorSearchOptions {
            k,
            include_vectors: true,
            include_metadata: true,
            ..Default::default()
        };
        
        let results = self.inner.search(&query, options)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
        
        Ok(results.into_iter().map(|r| {
            let id = format!("{:x}", r.id.0.iter().map(|b| format!("{:02x}", b)).collect::<String>());
            PyVectorSearchResult {
                id,
                score: r.score,
                vector: r.vector,
                metadata: r.metadata.map(|m| m.into_iter().collect()),
            }
        }).collect())
    }

    fn len(&self) -> usize {
        self.inner.len()
    }

    fn is_empty(&self) -> bool {
        self.inner.is_empty()
    }

    fn dimensions(&self) -> usize {
        self.inner.dimensions()
    }
}

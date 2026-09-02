use pyo3::prelude::*;
use std::collections::HashMap;

/// Python wrapper for VectorStore
#[pyclass]
pub struct PyVectorStore {
    inner: crate::VectorStore,
}

#[pymethods]
impl PyVectorStore {
    #[new]
    fn new(dimensions: usize) -> Self {
        Self {
            inner: crate::VectorStore::new(dimensions),
        }
    }

    fn add(&mut self, id: String, vector: Vec<f32>, metadata: Option<HashMap<String, String>>) -> PyResult<()> {
        self.inner.insert(crate::string_to_id(&id), vector, metadata)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e))
    }

    fn search(&self, query: Vec<f32>, k: usize) -> Vec<(String, f32)> {
        self.inner.search(&query, k)
            .into_iter()
            .map(|(id, score)| (crate::id_to_string(&id), score))
            .collect()
    }

    fn len(&self) -> usize {
        self.inner.len()
    }

    fn is_empty(&self) -> bool {
        self.inner.is_empty()
    }
}

/// Python wrapper for TextSplitter
#[pyclass]
pub struct PyTextSplitter {
    inner: crate::TextSplitter,
}

#[pymethods]
impl PyTextSplitter {
    #[new]
    #[pyo3(signature = (chunk_size=1000, chunk_overlap=200))]
    fn new(chunk_size: usize, chunk_overlap: usize) -> Self {
        Self {
            inner: crate::TextSplitter::new(chunk_size, chunk_overlap),
        }
    }

    fn split(&self, text: &str) -> Vec<String> {
        self.inner.split(text)
    }
}

/// Python wrapper for Tokenizer
#[pyclass]
pub struct PyTokenizer;

#[pymethods]
impl PyTokenizer {
    #[new]
    fn new() -> Self {
        Self
    }

    fn tokenize(&self, text: &str) -> Vec<String> {
        crate::Tokenizer::new().tokenize(text)
    }

    fn count_tokens(&self, text: &str) -> usize {
        crate::Tokenizer::new().count_tokens(text)
    }
}

/// Python module for Aeryn Engine
#[pymodule]
fn aeryn_engine(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;
    m.add_class::<PyVectorStore>()?;
    m.add_class::<PyTextSplitter>()?;
    m.add_class::<PyTokenizer>()?;
    Ok(())
}

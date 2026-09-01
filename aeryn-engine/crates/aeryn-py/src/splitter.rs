use pyo3::prelude::*;

#[pyclass]
pub struct PyTextSplitter {
    inner: aeryn_splitter::recursive::RecursiveCharacterTextSplitter,
}

#[pymethods]
impl PyTextSplitter {
    #[new]
    #[pyo3(signature = (chunk_size=1000, chunk_overlap=200))]
    fn new(chunk_size: usize, chunk_overlap: usize) -> Self {
        let config = aeryn_splitter::recursive::SplitterConfig {
            chunk_size,
            chunk_overlap,
            ..Default::default()
        };
        Self {
            inner: aeryn_splitter::recursive::RecursiveCharacterTextSplitter::new(config),
        }
    }

    fn split_text(&self, text: &str) -> Vec<String> {
        self.inner.split_text(text)
    }

    fn count_chunks(&self, text: &str) -> usize {
        self.inner.split_text(text).len()
    }
}

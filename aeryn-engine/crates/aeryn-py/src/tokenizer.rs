use pyo3::prelude::*;

#[pyclass]
pub struct PyTokenizer {
    inner: aeryn_tokenizer::Tokenizer,
}

#[pymethods]
impl PyTokenizer {
    #[new]
    fn new() -> Self {
        Self {
            inner: aeryn_tokenizer::Tokenizer::with_default_config(),
        }
    }

    fn count_tokens(&self, text: &str) -> usize {
        self.inner.count_tokens(text)
    }

    fn tokenize(&self, text: &str) -> Vec<String> {
        self.inner.tokenize(text)
    }
}

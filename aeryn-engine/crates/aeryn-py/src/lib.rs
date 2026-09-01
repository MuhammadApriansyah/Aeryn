//! Aeryn Python bindings — expose Rust engine to Python via PyO3.

use pyo3::prelude::*;

pub mod vector;
pub mod splitter;
pub mod tokenizer;

/// Aeryn Engine — high-performance AI agent engine.
#[pymodule]
fn aeryn_engine(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<vector::PyVectorIndex>()?;
    m.add_class::<vector::PyVectorSearchResult>()?;
    m.add_class::<splitter::PyTextSplitter>()?;
    m.add_class::<tokenizer::PyTokenizer>()?;
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;
    Ok(())
}

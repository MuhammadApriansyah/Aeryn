//! PyO3 bindings untuk Rust engine.

use pyo3::prelude::*;

pub mod vector;
pub mod splitter;
pub mod tokenizer;

#[pymodule]
fn aeryn_engine(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<vector::PyVectorStore>()?;
    m.add_class::<splitter::PyTextSplitter>()?;
    m.add_class::<tokenizer::PyTokenizer>()?;
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;
    Ok(())
}

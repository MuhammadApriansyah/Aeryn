//! Aeryn Core Engine — foundational types and utilities.
//!
//! This crate provides the core types, error handling, and utilities
//! used by all other Aeryn engine crates.

pub mod error;
pub mod types;
pub mod utils;

pub use error::{AerynError, AerynResult};
pub use types::*;
pub use utils::*;

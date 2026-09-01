use std::fmt;
use std::io;
use std::sync::Arc;

use thiserror::Error;

/// Result type for all Aeryn operations.
pub type AerynResult<T> = Result<T, AerynError>;

/// Error type for all Aeryn operations.
#[derive(Error, Debug)]
pub enum AerynError {
    #[error("IO error: {0}")]
    Io(String),

    #[error("Serialization error: {0}")]
    Serialization(String),

    #[error("Deserialization error: {0}")]
    Deserialization(String),

    #[error("Validation error: {0}")]
    Validation(String),

    #[error("Not found: {0}")]
    NotFound(String),

    #[error("Already exists: {0}")]
    AlreadyExists(String),

    #[error("Invalid input: {0}")]
    InvalidInput(String),

    #[error("Configuration error: {0}")]
    Config(String),

    #[error("Database error: {0}")]
    Database(String),

    #[error("Network error: {0}")]
    Network(String),

    #[error("Authentication error: {0}")]
    Authentication(String),

    #[error("Authorization error: {0}")]
    Authorization(String),

    #[error("Rate limit exceeded: {0}")]
    RateLimit(String),

    #[error("Timeout: {0}")]
    Timeout(String),

    #[error("Internal error: {0}")]
    Internal(String),

    #[error("Not implemented: {0}")]
    NotImplemented(String),

    #[error("External error: {source}")]
    External { source: std::sync::Arc<dyn std::error::Error + Send + Sync> },
}

impl From<io::Error> for AerynError {
    fn from(err: io::Error) -> Self {
        AerynError::Io(err.to_string())
    }
}

impl From<serde_json::Error> for AerynError {
    fn from(err: serde_json::Error) -> Self {
        AerynError::Serialization(err.to_string())
    }
}

impl From<rusqlite::Error> for AerynError {
    fn from(err: rusqlite::Error) -> Self {
        AerynError::Database(err.to_string())
    }
}

impl From<bincode::Error> for AerynError {
    fn from(err: bincode::Error) -> Self {
        AerynError::Serialization(err.to_string())
    }
}

impl From<base64::DecodeError> for AerynError {
    fn from(err: base64::DecodeError) -> Self {
        AerynError::Deserialization(err.to_string())
    }
}

impl From<regex::Error> for AerynError {
    fn from(err: regex::Error) -> Self {
        AerynError::Validation(format!("Regex error: {}", err.to_string()))
    }
}

impl From<std::str::Utf8Error> for AerynError {
    fn from(err: std::str::Utf8Error) -> Self {
        AerynError::Validation(format!("UTF-8 error: {}", err.to_string()))
    }
}

impl From<std::string::FromUtf8Error> for AerynError {
    fn from(err: std::string::FromUtf8Error) -> Self {
        AerynError::Validation(format!("UTF-8 error: {}", err.to_string()))
    }
}

/// Error context for chaining errors with additional information.
#[derive(Debug, Clone)]
pub struct ErrorContext {
    pub message: String,
    pub source: Option<Arc<AerynError>>,
}

impl ErrorContext {
    pub fn new(message: impl Into<String>) -> Self {
        Self {
            message: message.into(),
            source: None,
        }
    }

    pub fn with_source(message: impl Into<String>, source: AerynError) -> Self {
        Self {
            message: message.into(),
            source: Some(Arc::new(source)),
        }
    }
}

impl fmt::Display for ErrorContext {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.message)?;
        if let Some(ref source) = self.source {
            write!(f, " (caused by: {})", source)?;
        }
        Ok(())
    }
}

/// Macro for creating errors with context.
#[macro_export]
macro_rules! aeryn_err {
    ($variant:ident, $($arg:tt)*) => {
        $crate::AerynError::$variant(format!($($arg)*))
    };
}

/// Macro for wrapping errors with context.
#[macro_export]
macro_rules! aeryn_bail {
    ($variant:ident, $($arg:tt)*) => {
        return Err($crate::aeryn_err!($variant, $($arg)*))
    };
}

/// Macro for ensuring a condition is true.
#[macro_export]
macro_rules! aeryn_ensure {
    ($cond:expr, $variant:ident, $($arg:tt)*) => {
        if !$cond {
            return Err($crate::aeryn_err!($variant, $($arg)*));
        }
    };
}

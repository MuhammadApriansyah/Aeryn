use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ClientConfig {
    pub server_url: String,
    pub timeout_ms: u64,
}

pub struct MCPClientConfig;

impl MCPClientConfig {
    pub fn new() -> Self {
        Self
    }
}

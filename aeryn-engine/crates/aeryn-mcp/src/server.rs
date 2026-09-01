use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MCPMessage {
    pub id: String,
    pub method: String,
    pub params: HashMap<String, String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MCPRequest {
    pub id: String,
    pub method: String,
    pub params: HashMap<String, String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MCPResponse {
    pub id: String,
    pub result: Option<String>,
    pub error: Option<MCPError>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MCPError {
    pub code: i32,
    pub message: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolDefinition {
    pub name: String,
    pub description: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ResourceDefinition {
    pub uri: String,
    pub description: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PromptDefinition {
    pub name: String,
    pub description: String,
}

pub struct MCPServer;

impl MCPServer {
    pub fn new() -> Self {
        Self
    }
}

pub struct MCPClient;

impl MCPClient {
    pub fn new() -> Self {
        Self
    }
}

//! Core types used throughout the Aeryn engine.
//!
//! These types represent the fundamental data structures:
//! Documents, Embeddings, Chunks, Brains, etc.

use std::collections::HashMap;
use std::fmt;
use std::sync::Arc;

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// Unique identifier for entities.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct Id(pub [u8; 16]);

impl Id {
    pub fn new() -> Self {
        Uuid::new_v4().into()
    }

    pub fn nil() -> Self {
        Id([0u8; 16])
    }

    pub fn as_bytes(&self) -> &[u8; 16] {
        &self.0
    }
}

impl Default for Id {
    fn default() -> Self {
        Self::new()
    }
}

impl From<Uuid> for Id {
    fn from(uuid: Uuid) -> Self {
        Id(uuid.into_bytes())
    }
}

impl From<[u8; 16]> for Id {
    fn from(bytes: [u8; 16]) -> Self {
        Id(bytes)
    }
}

impl fmt::Display for Id {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", Uuid::from_bytes(self.0))
    }
}

/// Metadata attached to documents, chunks, and brains.
pub type Metadata = HashMap<String, Value>;

/// Value types for metadata.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum Value {
    Null,
    Bool(bool),
    Int(i64),
    Float(f64),
    String(String),
    Array(Vec<Value>),
    Object(HashMap<String, Value>),
}

impl Value {
    pub fn as_str(&self) -> Option<&str> {
        match self {
            Value::String(s) => Some(s.as_str()),
            _ => None,
        }
    }

    pub fn as_i64(&self) -> Option<i64> {
        match self {
            Value::Int(i) => Some(*i),
            _ => None,
        }
    }

    pub fn as_f64(&self) -> Option<f64> {
        match self {
            Value::Float(f) => Some(*f),
            _ => None,
        }
    }

    pub fn as_bool(&self) -> Option<bool> {
        match self {
            Value::Bool(b) => Some(*b),
            _ => None,
        }
    }

    pub fn as_array(&self) -> Option<&[Value]> {
        match self {
            Value::Array(arr) => Some(arr.as_slice()),
            _ => None,
        }
    }

    pub fn as_object(&self) -> Option<&HashMap<String, Value>> {
        match self {
            Value::Object(map) => Some(map),
            _ => None,
        }
    }
}

impl From<String> for Value {
    fn from(s: String) -> Self {
        Value::String(s)
    }
}

impl From<&str> for Value {
    fn from(s: &str) -> Self {
        Value::String(s.to_string())
    }
}

impl From<i64> for Value {
    fn from(i: i64) -> Self {
        Value::Int(i)
    }
}

impl From<f64> for Value {
    fn from(f: f64) -> Self {
        Value::Float(f)
    }
}

impl From<bool> for Value {
    fn from(b: bool) -> Self {
        Value::Bool(b)
    }
}

/// A document is a unit of text with metadata.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Document {
    pub id: Id,
    pub content: String,
    pub metadata: Metadata,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

impl Document {
    pub fn new(content: impl Into<String>) -> Self {
        let now = Utc::now();
        Self {
            id: Id::new(),
            content: content.into(),
            metadata: HashMap::new(),
            created_at: now,
            updated_at: now,
        }
    }

    pub fn with_id(id: Id, content: impl Into<String>) -> Self {
        let now = Utc::now();
        Self {
            id,
            content: content.into(),
            metadata: HashMap::new(),
            created_at: now,
            updated_at: now,
        }
    }

    pub fn with_metadata(mut self, key: impl Into<String>, value: impl Into<Value>) -> Self {
        self.metadata.insert(key.into(), value.into());
        self
    }

    pub fn set_metadata(&mut self, key: impl Into<String>, value: impl Into<Value>) {
        self.metadata.insert(key.into(), value.into());
    }

    pub fn get_metadata(&self, key: &str) -> Option<&Value> {
        self.metadata.get(key)
    }

    pub fn len(&self) -> usize {
        self.content.len()
    }

    pub fn is_empty(&self) -> bool {
        self.content.is_empty()
    }
}

/// A chunk is a smaller piece of a document.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Chunk {
    pub id: Id,
    pub document_id: Id,
    pub content: String,
    pub start_offset: usize,
    pub end_offset: usize,
    pub metadata: Metadata,
    pub embedding: Option<Vec<f32>>,
}

impl Chunk {
    pub fn new(
        document_id: Id,
        content: impl Into<String>,
        start_offset: usize,
        end_offset: usize,
    ) -> Self {
        Self {
            id: Id::new(),
            document_id,
            content: content.into(),
            start_offset,
            end_offset,
            metadata: HashMap::new(),
            embedding: None,
        }
    }

    pub fn with_embedding(mut self, embedding: Vec<f32>) -> Self {
        self.embedding = Some(embedding);
        self
    }

    pub fn set_embedding(&mut self, embedding: Vec<f32>) {
        self.embedding = Some(embedding);
    }

    pub fn has_embedding(&self) -> bool {
        self.embedding.is_some()
    }

    pub fn embedding(&self) -> Option<&[f32]> {
        self.embedding.as_deref()
    }
}

/// An embedding is a vector representation of text.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Embedding {
    pub id: Id,
    pub chunk_id: Id,
    pub vector: Vec<f32>,
    pub model: String,
    pub dimensions: usize,
    pub created_at: DateTime<Utc>,
}

impl Embedding {
    pub fn new(chunk_id: Id, vector: Vec<f32>, model: impl Into<String>) -> Self {
        let dimensions = vector.len();
        Self {
            id: Id::new(),
            chunk_id,
            vector,
            model: model.into(),
            dimensions,
            created_at: Utc::now(),
        }
    }

    pub fn cosine_similarity(&self, other: &Embedding) -> f32 {
        let dot_product: f32 = self
            .vector
            .iter()
            .zip(other.vector.iter())
            .map(|(a, b)| a * b)
            .sum();

        let norm_a: f32 = self.vector.iter().map(|x| x * x).sum::<f32>().sqrt();
        let norm_b: f32 = other.vector.iter().map(|x| x * x).sum::<f32>().sqrt();

        if norm_a == 0.0 || norm_b == 0.0 {
            0.0
        } else {
            dot_product / (norm_a * norm_b)
        }
    }

    pub fn euclidean_distance(&self, other: &Embedding) -> f32 {
        self.vector
            .iter()
            .zip(other.vector.iter())
            .map(|(a, b)| (a - b).powi(2))
            .sum::<f32>()
            .sqrt()
    }

    pub fn dot_product(&self, other: &Embedding) -> f32 {
        self.vector
            .iter()
            .zip(other.vector.iter())
            .map(|(a, b)| a * b)
            .sum()
    }
}

/// A search result with score.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SearchResult {
    pub chunk: Chunk,
    pub score: f32,
    pub rank: usize,
}

impl SearchResult {
    pub fn new(chunk: Chunk, score: f32, rank: usize) -> Self {
        Self { chunk, score, rank }
    }
}

/// A brain is a collection of knowledge.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Brain {
    pub id: Id,
    pub name: String,
    pub description: String,
    pub documents: Vec<Document>,
    pub chunks: Vec<Chunk>,
    pub embeddings: Vec<Embedding>,
    pub metadata: Metadata,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

impl Brain {
    pub fn new(name: impl Into<String>) -> Self {
        let now = Utc::now();
        Self {
            id: Id::new(),
            name: name.into(),
            description: String::new(),
            documents: Vec::new(),
            chunks: Vec::new(),
            embeddings: Vec::new(),
            metadata: HashMap::new(),
            created_at: now,
            updated_at: now,
        }
    }

    pub fn with_description(mut self, description: impl Into<String>) -> Self {
        self.description = description.into();
        self
    }

    pub fn add_document(&mut self, document: Document) {
        self.documents.push(document);
        self.updated_at = Utc::now();
    }

    pub fn add_chunk(&mut self, chunk: Chunk) {
        self.chunks.push(chunk);
        self.updated_at = Utc::now();
    }

    pub fn add_embedding(&mut self, embedding: Embedding) {
        self.embeddings.push(embedding);
        self.updated_at = Utc::now();
    }

    pub fn document_count(&self) -> usize {
        self.documents.len()
    }

    pub fn chunk_count(&self) -> usize {
        self.chunks.len()
    }

    pub fn embedding_count(&self) -> usize {
        self.embeddings.len()
    }

    pub fn is_empty(&self) -> bool {
        self.documents.is_empty() && self.chunks.is_empty()
    }
}

/// Configuration for the engine.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EngineConfig {
    pub vector_dimension: usize,
    pub max_concurrent_tasks: usize,
    pub cache_size: usize,
    pub log_level: String,
    pub enable_metrics: bool,
}

impl Default for EngineConfig {
    fn default() -> Self {
        Self {
            vector_dimension: 1536,
            max_concurrent_tasks: num_cpus::get(),
            cache_size: 10_000,
            log_level: "info".to_string(),
            enable_metrics: true,
        }
    }
}

/// Statistics for the engine.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EngineStats {
    pub total_documents: u64,
    pub total_chunks: u64,
    pub total_embeddings: u64,
    pub total_searches: u64,
    pub total_index_time_ms: u64,
    pub total_search_time_ms: u64,
    pub cache_hits: u64,
    pub cache_misses: u64,
}

impl Default for EngineStats {
    fn default() -> Self {
        Self {
            total_documents: 0,
            total_chunks: 0,
            total_embeddings: 0,
            total_searches: 0,
            total_index_time_ms: 0,
            total_search_time_ms: 0,
            cache_hits: 0,
            cache_misses: 0,
        }
    }
}

/// A chat message in a conversation.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChatMessage {
    pub id: Id,
    pub role: MessageRole,
    pub content: String,
    pub metadata: Metadata,
    pub created_at: DateTime<Utc>,
}

impl ChatMessage {
    pub fn user(content: impl Into<String>) -> Self {
        Self {
            id: Id::new(),
            role: MessageRole::User,
            content: content.into(),
            metadata: HashMap::new(),
            created_at: Utc::now(),
        }
    }

    pub fn assistant(content: impl Into<String>) -> Self {
        Self {
            id: Id::new(),
            role: MessageRole::Assistant,
            content: content.into(),
            metadata: HashMap::new(),
            created_at: Utc::now(),
        }
    }

    pub fn system(content: impl Into<String>) -> Self {
        Self {
            id: Id::new(),
            role: MessageRole::System,
            content: content.into(),
            metadata: HashMap::new(),
            created_at: Utc::now(),
        }
    }
}

/// Role of a chat message.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum MessageRole {
    User,
    Assistant,
    System,
}

impl fmt::Display for MessageRole {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            MessageRole::User => write!(f, "user"),
            MessageRole::Assistant => write!(f, "assistant"),
            MessageRole::System => write!(f, "system"),
        }
    }
}

/// A conversation is a sequence of chat messages.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Conversation {
    pub id: Id,
    pub brain_id: Id,
    pub messages: Vec<ChatMessage>,
    pub metadata: Metadata,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

impl Conversation {
    pub fn new(brain_id: Id) -> Self {
        let now = Utc::now();
        Self {
            id: Id::new(),
            brain_id,
            messages: Vec::new(),
            metadata: HashMap::new(),
            created_at: now,
            updated_at: now,
        }
    }

    pub fn add_message(&mut self, message: ChatMessage) {
        self.messages.push(message);
        self.updated_at = Utc::now();
    }

    pub fn last_message(&self) -> Option<&ChatMessage> {
        self.messages.last()
    }

    pub fn message_count(&self) -> usize {
        self.messages.len()
    }

    pub fn is_empty(&self) -> bool {
        self.messages.is_empty()
    }
}

/// File processing result.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProcessedFile {
    pub path: String,
    pub file_type: FileType,
    pub documents: Vec<Document>,
    pub chunks: Vec<Chunk>,
    pub metadata: Metadata,
    pub processing_time_ms: u64,
}

impl ProcessedFile {
    pub fn new(path: impl Into<String>, file_type: FileType) -> Self {
        Self {
            path: path.into(),
            file_type,
            documents: Vec::new(),
            chunks: Vec::new(),
            metadata: HashMap::new(),
            processing_time_ms: 0,
        }
    }

    pub fn document_count(&self) -> usize {
        self.documents.len()
    }

    pub fn chunk_count(&self) -> usize {
        self.chunks.len()
    }
}

/// Supported file types.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum FileType {
    Text,
    Markdown,
    Pdf,
    Docx,
    Epub,
    Odt,
    Html,
    Json,
    Csv,
    Unknown,
}

impl FileType {
    pub fn from_extension(ext: &str) -> Self {
        match ext.to_lowercase().as_str() {
            "txt" => FileType::Text,
            "md" | "markdown" => FileType::Markdown,
            "pdf" => FileType::Pdf,
            "docx" => FileType::Docx,
            "epub" => FileType::Epub,
            "odt" => FileType::Odt,
            "html" | "htm" => FileType::Html,
            "json" => FileType::Json,
            "csv" => FileType::Csv,
            _ => FileType::Unknown,
        }
    }

    pub fn is_supported(&self) -> bool {
        !matches!(self, FileType::Unknown)
    }

    pub fn mime_type(&self) -> &'static str {
        match self {
            FileType::Text => "text/plain",
            FileType::Markdown => "text/markdown",
            FileType::Pdf => "application/pdf",
            FileType::Docx => "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            FileType::Epub => "application/epub+zip",
            FileType::Odt => "application/vnd.oasis.opendocument.text",
            FileType::Html => "text/html",
            FileType::Json => "application/json",
            FileType::Csv => "text/csv",
            FileType::Unknown => "application/octet-stream",
        }
    }
}

impl fmt::Display for FileType {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            FileType::Text => write!(f, "text"),
            FileType::Markdown => write!(f, "markdown"),
            FileType::Pdf => write!(f, "pdf"),
            FileType::Docx => write!(f, "docx"),
            FileType::Epub => write!(f, "epub"),
            FileType::Odt => write!(f, "odt"),
            FileType::Html => write!(f, "html"),
            FileType::Json => write!(f, "json"),
            FileType::Csv => write!(f, "csv"),
            FileType::Unknown => write!(f, "unknown"),
        }
    }
}

/// A plugin manifest.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PluginManifest {
    pub name: String,
    pub version: String,
    pub description: String,
    pub author: String,
    pub entry_point: String,
    pub dependencies: Vec<String>,
    pub permissions: Vec<String>,
    pub tags: Vec<String>,
}

impl PluginManifest {
    pub fn validate(&self) -> crate::AerynResult<()> {
        if self.name.is_empty() {
            return Err(crate::aeryn_err!(Validation, "Plugin name cannot be empty"));
        }
        if self.version.is_empty() {
            return Err(crate::aeryn_err!(Validation, "Plugin version cannot be empty"));
        }
        if self.entry_point.is_empty() {
            return Err(crate::aeryn_err!(
                Validation,
                "Plugin entry_point cannot be empty"
            ));
        }
        Ok(())
    }
}

/// A skill definition.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SkillDefinition {
    pub name: String,
    pub description: String,
    pub version: String,
    pub author: String,
    pub dependencies: Vec<String>,
    pub entry_point: String,
    pub tests: Vec<String>,
}

impl SkillDefinition {
    pub fn validate(&self) -> crate::AerynResult<()> {
        if self.name.is_empty() {
            return Err(crate::aeryn_err!(Validation, "Skill name cannot be empty"));
        }
        if self.version.is_empty() {
            return Err(crate::aeryn_err!(Validation, "Skill version cannot be empty"));
        }
        if self.entry_point.is_empty() {
            return Err(crate::aeryn_err!(
                Validation,
                "Skill entry_point cannot be empty"
            ));
        }
        Ok(())
    }
}

/// A workflow definition.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkflowDefinition {
    pub id: Id,
    pub name: String,
    pub description: String,
    pub nodes: Vec<WorkflowNode>,
    pub edges: Vec<WorkflowEdge>,
    pub metadata: Metadata,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

impl WorkflowDefinition {
    pub fn new(name: impl Into<String>) -> Self {
        let now = Utc::now();
        Self {
            id: Id::new(),
            name: name.into(),
            description: String::new(),
            nodes: Vec::new(),
            edges: Vec::new(),
            metadata: HashMap::new(),
            created_at: now,
            updated_at: now,
        }
    }

    pub fn add_node(&mut self, node: WorkflowNode) {
        self.nodes.push(node);
        self.updated_at = Utc::now();
    }

    pub fn add_edge(&mut self, edge: WorkflowEdge) {
        self.edges.push(edge);
        self.updated_at = Utc::now();
    }

    pub fn node_count(&self) -> usize {
        self.nodes.len()
    }

    pub fn edge_count(&self) -> usize {
        self.edges.len()
    }
}

/// A node in a workflow.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkflowNode {
    pub id: String,
    pub node_type: WorkflowNodeType,
    pub config: HashMap<String, Value>,
}

impl WorkflowNode {
    pub fn new(id: impl Into<String>, node_type: WorkflowNodeType) -> Self {
        Self {
            id: id.into(),
            node_type,
            config: HashMap::new(),
        }
    }

    pub fn with_config(mut self, key: impl Into<String>, value: impl Into<Value>) -> Self {
        self.config.insert(key.into(), value.into());
        self
    }
}

/// Types of workflow nodes.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum WorkflowNodeType {
    Llm,
    Retrieval,
    Tool,
    Condition,
    Input,
    Output,
    Transform,
}

impl fmt::Display for WorkflowNodeType {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            WorkflowNodeType::Llm => write!(f, "llm"),
            WorkflowNodeType::Retrieval => write!(f, "retrieval"),
            WorkflowNodeType::Tool => write!(f, "tool"),
            WorkflowNodeType::Condition => write!(f, "condition"),
            WorkflowNodeType::Input => write!(f, "input"),
            WorkflowNodeType::Output => write!(f, "output"),
            WorkflowNodeType::Transform => write!(f, "transform"),
        }
    }
}

/// An edge connecting two workflow nodes.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkflowEdge {
    pub source: String,
    pub target: String,
    pub condition: Option<String>,
}

impl WorkflowEdge {
    pub fn new(source: impl Into<String>, target: impl Into<String>) -> Self {
        Self {
            source: source.into(),
            target: target.into(),
            condition: None,
        }
    }

    pub fn with_condition(mut self, condition: impl Into<String>) -> Self {
        self.condition = Some(condition.into());
        self
    }
}

/// MCP protocol message.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MCPMessage {
    pub id: String,
    pub method: String,
    pub params: HashMap<String, Value>,
}

impl MCPMessage {
    pub fn new(id: impl Into<String>, method: impl Into<String>) -> Self {
        Self {
            id: id.into(),
            method: method.into(),
            params: HashMap::new(),
        }
    }

    pub fn with_param(mut self, key: impl Into<String>, value: impl Into<Value>) -> Self {
        self.params.insert(key.into(), value.into());
        self
    }
}

/// MCP response.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MCPResponse {
    pub id: String,
    pub result: Option<Value>,
    pub error: Option<MCPError>,
}

impl MCPResponse {
    pub fn success(id: impl Into<String>, result: impl Into<Value>) -> Self {
        Self {
            id: id.into(),
            result: Some(result.into()),
            error: None,
        }
    }

    pub fn error(id: impl Into<String>, code: i32, message: impl Into<String>) -> Self {
        Self {
            id: id.into(),
            result: None,
            error: Some(MCPError {
                code,
                message: message.into(),
            }),
        }
    }
}

/// MCP error.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MCPError {
    pub code: i32,
    pub message: String,
}

/// Graph node for knowledge graph.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GraphNode {
    pub id: Id,
    pub label: String,
    pub node_type: GraphNodeType,
    pub metadata: Metadata,
}

impl GraphNode {
    pub fn new(label: impl Into<String>, node_type: GraphNodeType) -> Self {
        Self {
            id: Id::new(),
            label: label.into(),
            node_type,
            metadata: HashMap::new(),
        }
    }
}

/// Types of graph nodes.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum GraphNodeType {
    Entity,
    Concept,
    Event,
    Document,
    Chunk,
}

impl fmt::Display for GraphNodeType {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            GraphNodeType::Entity => write!(f, "entity"),
            GraphNodeType::Concept => write!(f, "concept"),
            GraphNodeType::Event => write!(f, "event"),
            GraphNodeType::Document => write!(f, "document"),
            GraphNodeType::Chunk => write!(f, "chunk"),
        }
    }
}

/// Graph edge for knowledge graph.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GraphEdge {
    pub source_id: Id,
    pub target_id: Id,
    pub edge_type: GraphEdgeType,
    pub weight: f32,
    pub metadata: Metadata,
}

impl GraphEdge {
    pub fn new(source_id: Id, target_id: Id, edge_type: GraphEdgeType) -> Self {
        Self {
            source_id,
            target_id,
            edge_type,
            weight: 1.0,
            metadata: HashMap::new(),
        }
    }

    pub fn with_weight(mut self, weight: f32) -> Self {
        self.weight = weight;
        self
    }
}

/// Types of graph edges.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum GraphEdgeType {
    RelatedTo,
    Supersedes,
    DependsOn,
    Contradicts,
    Extends,
    Causes,
    Contains,
    References,
}

impl fmt::Display for GraphEdgeType {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            GraphEdgeType::RelatedTo => write!(f, "related_to"),
            GraphEdgeType::Supersedes => write!(f, "supersedes"),
            GraphEdgeType::DependsOn => write!(f, "depends_on"),
            GraphEdgeType::Contradicts => write!(f, "contradicts"),
            GraphEdgeType::Extends => write!(f, "extends"),
            GraphEdgeType::Causes => write!(f, "causes"),
            GraphEdgeType::Contains => write!(f, "contains"),
            GraphEdgeType::References => write!(f, "references"),
        }
    }
}

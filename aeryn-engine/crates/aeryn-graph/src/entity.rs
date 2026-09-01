//! Entity extraction and typing.

use std::collections::HashMap;

use serde::{Deserialize, Serialize};

use aeryn_core::types::{GraphNode, GraphNodeType, Id};

/// Entity types for classification.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum EntityType {
    Person,
    Organization,
    Location,
    Date,
    Time,
    Money,
    Percent,
    Product,
    Event,
    WorkOfArt,
    Law,
    Language,
    Quantity,
    Ordinal,
    Cardinal,
    Concept,
    Technology,
    Method,
    Custom,
}

impl EntityType {
    pub fn from_str(s: &str) -> Option<Self> {
        match s.to_lowercase().as_str() {
            "person" | "per" => Some(EntityType::Person),
            "organization" | "org" => Some(EntityType::Organization),
            "location" | "loc" => Some(EntityType::Location),
            "date" => Some(EntityType::Date),
            "time" => Some(EntityType::Time),
            "money" => Some(EntityType::Money),
            "percent" => Some(EntityType::Percent),
            "product" => Some(EntityType::Product),
            "event" => Some(EntityType::Event),
            "work_of_art" | "art" => Some(EntityType::WorkOfArt),
            "law" => Some(EntityType::Law),
            "language" | "lang" => Some(EntityType::Language),
            "quantity" | "quant" => Some(EntityType::Quantity),
            "ordinal" => Some(EntityType::Ordinal),
            "cardinal" => Some(EntityType::Cardinal),
            "concept" => Some(EntityType::Concept),
            "technology" | "tech" => Some(EntityType::Technology),
            "method" => Some(EntityType::Method),
            _ => Some(EntityType::Custom),
        }
    }

    pub fn to_graph_node_type(&self) -> GraphNodeType {
        match self {
            EntityType::Concept => GraphNodeType::Concept,
            EntityType::Event => GraphNodeType::Event,
            _ => GraphNodeType::Entity,
        }
    }
}

/// An extracted entity.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Entity {
    pub id: Id,
    pub name: String,
    pub entity_type: EntityType,
    pub confidence: f32,
    pub start_offset: usize,
    pub end_offset: usize,
    pub metadata: HashMap<String, String>,
}

impl Entity {
    pub fn new(name: impl Into<String>, entity_type: EntityType) -> Self {
        Self {
            id: Id::new(),
            name: name.into(),
            entity_type,
            confidence: 1.0,
            start_offset: 0,
            end_offset: 0,
            metadata: HashMap::new(),
        }
    }

    pub fn with_confidence(mut self, confidence: f32) -> Self {
        self.confidence = confidence;
        self
    }

    pub fn with_offsets(mut self, start: usize, end: usize) -> Self {
        self.start_offset = start;
        self.end_offset = end;
        self
    }

    pub fn to_graph_node(&self) -> GraphNode {
        let mut node = GraphNode::new(&self.name, self.entity_type.to_graph_node_type());
        node.metadata.insert("confidence".to_string(), self.confidence.to_string());
        node.metadata.insert("entity_type".to_string(), format!("{:?}", self.entity_type));
        node
    }
}

/// Entity extractor — identifies and classifies entities in text.
pub struct EntityExtractor {
    patterns: HashMap<EntityType, Vec<String>>,
}

impl EntityExtractor {
    pub fn new() -> Self {
        let mut patterns = HashMap::new();
        
        // Simple regex patterns for common entities
        patterns.insert(EntityType::Date, vec![
            r"\b\d{4}-\d{2}-\d{2}\b".to_string(),
            r"\b\d{1,2}/\d{1,2}/\d{4}\b".to_string(),
            r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b".to_string(),
        ]);

        patterns.insert(EntityType::Time, vec![
            r"\b\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)?\b".to_string(),
        ]);

        patterns.insert(EntityType::Money, vec![
            r"\$[\d,]+\.?\d*".to_string(),
            r"\b\d+\s*(?:dollars?|USD|EUR|GBP)\b".to_string(),
        ]);

        patterns.insert(EntityType::Percent, vec![
            r"\b\d+\.?\d*\s*%".to_string(),
        ]);

        patterns.insert(EntityType::Email, vec![
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b".to_string(),
        ]);

        patterns.insert(EntityType::Url, vec![
            r"https?://[^\s]+".to_string(),
            r"www\.[^\s]+".to_string(),
        ]);

        Self { patterns }
    }

    pub fn extract(&self, text: &str) -> Vec<Entity> {
        let mut entities = Vec::new();

        for (entity_type, patterns) in &self.patterns {
            for pattern in patterns {
                if let Ok(re) = regex::Regex::new(pattern) {
                    for mat in re.find_iter(text) {
                        entities.push(Entity::new(
                            mat.as_str(),
                            *entity_type,
                        ).with_offsets(mat.start(), mat.end()));
                    }
                }
            }
        }

        entities
    }

    pub fn extract_with_context(&self, text: &str, context_window: usize) -> Vec<(Entity, String)> {
        self.extract(text)
            .into_iter()
            .map(|entity| {
                let context_start = entity.start_offset.saturating_sub(context_window);
                let context_end = (entity.end_offset + context_window).min(text.len());
                let context = text[context_start..context_end].to_string();
                (entity, context)
            })
            .collect()
    }

    pub fn register_pattern(&mut self, entity_type: EntityType, pattern: impl Into<String>) {
        self.patterns.entry(entity_type).or_insert_with(Vec::new).push(pattern.into());
    }
}

impl Default for EntityExtractor {
    fn default() -> Self {
        Self::new()
    }
}

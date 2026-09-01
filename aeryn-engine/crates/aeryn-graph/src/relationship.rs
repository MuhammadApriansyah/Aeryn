//! Relationship extraction and typing.

use std::collections::HashMap;

use serde::{Deserialize, Serialize};

use aeryn_core::types::{GraphEdge, GraphEdgeType, Id};

/// Relationship types between entities.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum RelationshipType {
    IsA,
    PartOf,
    HasA,
    CreatedBy,
    UsedBy,
    LocatedIn,
    RelatedTo,
    DependsOn,
    Causes,
    Antonym,
    Synonym,
    InstanceOf,
    SubclassOf,
    HasProperty,
    MadeFrom,
    UsedFor,
    CapableOf,
    ReceivesAction,
    AtProperty,
    Custom,
}

impl RelationshipType {
    pub fn from_str(s: &str) -> Option<Self> {
        match s.to_lowercase().as_str() {
            "isa" | "is_a" => Some(RelationshipType::IsA),
            "partof" | "part_of" => Some(RelationshipType::PartOf),
            "hasa" | "has_a" => Some(RelationshipType::HasA),
            "createdby" | "created_by" => Some(RelationshipType::CreatedBy),
            "usedby" | "used_by" => Some(RelationshipType::UsedBy),
            "locatedin" | "located_in" => Some(RelationshipType::LocatedIn),
            "relatedto" | "related_to" => Some(RelationshipType::RelatedTo),
            "dependson" | "depends_on" => Some(RelationshipType::DependsOn),
            "causes" => Some(RelationshipType::Causes),
            "antonym" => Some(RelationshipType::Antonym),
            "synonym" => Some(RelationshipType::Synonym),
            "instanceof" | "instance_of" => Some(RelationshipType::InstanceOf),
            "subclassof" | "subclass_of" => Some(RelationshipType::SubclassOf),
            "hasproperty" | "has_property" => Some(RelationshipType::HasProperty),
            "madefrom" | "made_from" => Some(RelationshipType::MadeFrom),
            "usedfor" | "used_for" => Some(RelationshipType::UsedFor),
            "capableof" | "capable_of" => Some(RelationshipType::CapableOf),
            "receivesaction" | "receives_action" => Some(RelationshipType::ReceivesAction),
            "atproperty" | "at_property" => Some(RelationshipType::AtProperty),
            _ => Some(RelationshipType::Custom),
        }
    }

    pub fn to_graph_edge_type(&self) -> GraphEdgeType {
        match self {
            RelationshipType::IsA => GraphEdgeType::RelatedTo,
            RelationshipType::PartOf => GraphEdgeType::Contains,
            RelationshipType::HasA => GraphEdgeType::RelatedTo,
            RelationshipType::CreatedBy => GraphEdgeType::RelatedTo,
            RelationshipType::UsedBy => GraphEdgeType::RelatedTo,
            RelationshipType::LocatedIn => GraphEdgeType::RelatedTo,
            RelationshipType::RelatedTo => GraphEdgeType::RelatedTo,
            RelationshipType::DependsOn => GraphEdgeType::DependsOn,
            RelationshipType::Causes => GraphEdgeType::Causes,
            RelationshipType::Antonym => GraphEdgeType::Contradicts,
            RelationshipType::Synonym => GraphEdgeType::RelatedTo,
            RelationshipType::InstanceOf => GraphEdgeType::RelatedTo,
            RelationshipType::SubclassOf => GraphEdgeType::Extends,
            RelationshipType::HasProperty => GraphEdgeType::RelatedTo,
            RelationshipType::MadeFrom => GraphEdgeType::RelatedTo,
            RelationshipType::UsedFor => GraphEdgeType::RelatedTo,
            RelationshipType::CapableOf => GraphEdgeType::RelatedTo,
            RelationshipType::ReceivesAction => GraphEdgeType::RelatedTo,
            RelationshipType::AtProperty => GraphEdgeType::RelatedTo,
            RelationshipType::Custom => GraphEdgeType::RelatedTo,
        }
    }
}

/// An extracted relationship.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Relationship {
    pub id: Id,
    pub source_id: Id,
    pub target_id: Id,
    pub relationship_type: RelationshipType,
    pub confidence: f32,
    pub metadata: HashMap<String, String>,
}

impl Relationship {
    pub fn new(source_id: Id, target_id: Id, relationship_type: RelationshipType) -> Self {
        Self {
            id: Id::new(),
            source_id,
            target_id,
            relationship_type,
            confidence: 1.0,
            metadata: HashMap::new(),
        }
    }

    pub fn with_confidence(mut self, confidence: f32) -> Self {
        self.confidence = confidence;
        self
    }

    pub fn to_graph_edge(&self) -> GraphEdge {
        let mut edge = GraphEdge::new(self.source_id, self.target_id, self.relationship_type.to_graph_edge_type());
        edge.weight = self.confidence;
        edge
    }
}

/// Relationship extractor — identifies relationships between entities.
pub struct RelationshipExtractor {
    patterns: HashMap<RelationshipType, Vec<(String, String)>>,
}

impl RelationshipExtractor {
    pub fn new() -> Self {
        let mut patterns = HashMap::new();

        // Simple pattern-based extraction
        patterns.insert(RelationshipType::IsA, vec![
            r"(\w+)\s+is\s+a\s+(\w+)".to_string(),
            r"(\w+)\s+are\s+(\w+)".to_string(),
        ]);

        patterns.insert(RelationshipType::PartOf, vec![
            r"(\w+)\s+is\s+part\s+of\s+(\w+)".to_string(),
            r"(\w+)\s+belongs?\s+to\s+(\w+)".to_string(),
        ]);

        patterns.insert(RelationshipType::HasA, vec![
            r"(\w+)\s+has\s+a\s+(\w+)".to_string(),
            r"(\w+)\s+have\s+(\w+)".to_string(),
        ]);

        patterns.insert(RelationshipType::CreatedBy, vec![
            r"(\w+)\s+was\s+created\s+by\s+(\w+)".to_string(),
            r"(\w+)\s+created\s+(\w+)".to_string(),
        ]);

        patterns.insert(RelationshipType::LocatedIn, vec![
            r"(\w+)\s+is\s+located\s+in\s+(\w+)".to_string(),
            r"(\w+)\s+is\s+in\s+(\w+)".to_string(),
        ]);

        Self { patterns }
    }

    pub fn extract(&self, text: &str) -> Vec<Relationship> {
        let mut relationships = Vec::new();

        for (rel_type, patterns) in &self.patterns {
            for pattern in patterns {
                if let Ok(re) = regex::Regex::new(pattern) {
                    for cap in re.captures_iter(text) {
                        if cap.len() >= 3 {
                            let source = cap.get(1).unwrap().as_str().to_string();
                            let target = cap.get(2).unwrap().as_str().to_string();
                            
                            // Create temporary IDs (would be resolved against actual entities)
                            let source_id = Id::from(source.as_bytes()[..16.min(source.len())].try_into().unwrap_or([0u8; 16]));
                            let target_id = Id::from(target.as_bytes()[..16.min(target.len())].try_into().unwrap_or([0u8; 16]));
                            
                            relationships.push(Relationship::new(source_id, target_id, *rel_type));
                        }
                    }
                }
            }
        }

        relationships
    }

    pub fn register_pattern(&mut self, rel_type: RelationshipType, pattern: impl Into<String>) {
        self.patterns.entry(rel_type).or_insert_with(Vec::new).push((pattern.into(), String::new()));
    }
}

impl Default for RelationshipExtractor {
    fn default() -> Self {
        Self::new()
    }
}

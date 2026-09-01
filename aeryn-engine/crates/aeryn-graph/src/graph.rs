//! Knowledge graph implementation.

use std::collections::{HashMap, HashSet, VecDeque};

use serde::{Deserialize, Serialize};
use tracing::{debug, info, instrument};

use aeryn_core::error::{AerynError, AerynResult};
use aeryn_core::types::{GraphEdge, GraphEdgeType, GraphNode, GraphNodeType, Id};

/// Configuration for the knowledge graph.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GraphConfig {
    /// Maximum number of nodes.
    pub max_nodes: usize,
    /// Maximum number of edges per node.
    pub max_edges_per_node: usize,
    /// Whether to auto-detect relationships.
    pub auto_detect_relationships: bool,
    /// Minimum confidence for auto-detected relationships.
    pub min_confidence: f32,
}

impl Default for GraphConfig {
    fn default() -> Self {
        Self {
            max_nodes: 100_000,
            max_edges_per_node: 100,
            auto_detect_relationships: true,
            min_confidence: 0.5,
        }
    }
}

/// Statistics about the knowledge graph.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GraphStats {
    pub node_count: usize,
    pub edge_count: usize,
    pub entity_count: usize,
    pub concept_count: usize,
    pub document_count: usize,
    pub avg_degree: f64,
    pub max_degree: usize,
}

/// Knowledge graph for entity-relationship storage.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KnowledgeGraph {
    config: GraphConfig,
    nodes: HashMap<Id, GraphNode>,
    edges: Vec<GraphEdge>,
    adjacency: HashMap<Id, Vec<Id>>,
    reverse_adjacency: HashMap<Id, Vec<Id>>,
}

impl KnowledgeGraph {
    pub fn new(config: GraphConfig) -> Self {
        Self {
            config,
            nodes: HashMap::new(),
            edges: Vec::new(),
            adjacency: HashMap::new(),
            reverse_adjacency: HashMap::new(),
        }
    }

    pub fn with_default_config() -> Self {
        Self::new(GraphConfig::default())
    }

    pub fn add_node(&mut self, node: GraphNode) -> AerynResult<()> {
        if self.nodes.len() >= self.config.max_nodes {
            return Err(AerynError::Validation("Graph is full".to_string()));
        }
        self.nodes.insert(node.id, node);
        self.adjacency.entry(node.id).or_insert_with(Vec::new);
        self.reverse_adjacency.entry(node.id).or_insert_with(Vec::new);
        Ok(())
    }

    pub fn add_edge(&mut self, edge: GraphEdge) -> AerynResult<()> {
        if !self.nodes.contains_key(&edge.source_id) || !self.nodes.contains_key(&edge.target_id) {
            return Err(AerynError::NotFound("Source or target node not found".to_string()));
        }

        let source_degree = self.adjacency.get(&edge.source_id).map(|v| v.len()).unwrap_or(0);
        if source_degree >= self.config.max_edges_per_node {
            return Err(AerynError::Validation("Source node has too many edges".to_string()));
        }

        self.edges.push(edge.clone());
        self.adjacency.entry(edge.source_id).or_insert_with(Vec::new).push(edge.target_id);
        self.reverse_adjacency.entry(edge.target_id).or_insert_with(Vec::new).push(edge.source_id);
        Ok(())
    }

    pub fn get_node(&self, id: &Id) -> Option<&GraphNode> {
        self.nodes.get(id)
    }

    pub fn get_neighbors(&self, id: &Id) -> Vec<&GraphNode> {
        self.adjacency.get(id)
            .map(|neighbors| neighbors.iter().filter_map(|id| self.nodes.get(id)).collect())
            .unwrap_or_default()
    }

    pub fn get_incoming(&self, id: &Id) -> Vec<&GraphNode> {
        self.reverse_adjacency.get(id)
            .map(|neighbors| neighbors.iter().filter_map(|id| self.nodes.get(id)).collect())
            .unwrap_or_default()
    }

    pub fn bfs(&self, start: &Id, max_depth: usize) -> Vec<&GraphNode> {
        let mut visited = HashSet::new();
        let mut result = Vec::new();
        let mut queue = VecDeque::new();

        if self.nodes.contains_key(start) {
            queue.push_back((start, 0));
            visited.insert(*start);
        }

        while let Some((node_id, depth)) = queue.pop_front() {
            if depth > max_depth {
                continue;
            }
            if let Some(node) = self.nodes.get(node_id) {
                result.push(node);
                if let Some(neighbors) = self.adjacency.get(node_id) {
                    for neighbor in neighbors {
                        if !visited.contains(neighbor) {
                            visited.insert(*neighbor);
                            queue.push_back((neighbor, depth + 1));
                        }
                    }
                }
            }
        }

        result
    }

    pub fn dfs(&self, start: &Id, max_depth: usize) -> Vec<&GraphNode> {
        let mut visited = HashSet::new();
        let mut result = Vec::new();
        self.dfs_helper(start, max_depth, 0, &mut visited, &mut result);
        result
    }

    fn dfs_helper<'a>(
        &'a self,
        node_id: &Id,
        max_depth: usize,
        depth: usize,
        visited: &mut HashSet<Id>,
        result: &mut Vec<&'a GraphNode>,
    ) {
        if depth > max_depth || visited.contains(node_id) {
            return;
        }
        visited.insert(*node_id);
        if let Some(node) = self.nodes.get(node_id) {
            result.push(node);
            if let Some(neighbors) = self.adjacency.get(node_id) {
                for neighbor in neighbors {
                    self.dfs_helper(neighbor, max_depth, depth + 1, visited, result);
                }
            }
        }
    }

    pub fn find_path(&self, source: &Id, target: &Id, max_depth: usize) -> Option<Vec<Id>> {
        let mut visited = HashSet::new();
        let mut parent = HashMap::new();
        let mut queue = VecDeque::new();

        queue.push_back(*source);
        visited.insert(*source);

        while let Some(current) = queue.pop_front() {
            if current == *target {
                let mut path = vec![*target];
                let mut node = *target;
                while let Some(p) = parent.get(&node) {
                    path.push(*p);
                    node = *p;
                }
                path.reverse();
                return Some(path);
            }

            if let Some(neighbors) = self.adjacency.get(&current) {
                for neighbor in neighbors {
                    if !visited.contains(neighbor) {
                        visited.insert(*neighbor);
                        parent.insert(*neighbor, current);
                        queue.push_back(*neighbor);
                    }
                }
            }
        }

        None
    }

    pub fn stats(&self) -> GraphStats {
        let entity_count = self.nodes.values().filter(|n| n.node_type == GraphNodeType::Entity).count();
        let concept_count = self.nodes.values().filter(|n| n.node_type == GraphNodeType::Concept).count();
        let document_count = self.nodes.values().filter(|n| n.node_type == GraphNodeType::Document).count();

        let degrees: Vec<usize> = self.adjacency.values().map(|v| v.len()).collect();
        let max_degree = degrees.iter().copied().max().unwrap_or(0);
        let avg_degree = if !degrees.is_empty() {
            degrees.iter().sum::<usize>() as f64 / degrees.len() as f64
        } else {
            0.0
        };

        GraphStats {
            node_count: self.nodes.len(),
            edge_count: self.edges.len(),
            entity_count,
            concept_count,
            document_count,
            avg_degree,
            max_degree,
        }
    }

    pub fn len(&self) -> usize {
        self.nodes.len()
    }

    pub fn is_empty(&self) -> bool {
        self.nodes.is_empty()
    }

    pub fn remove_node(&mut self, id: &Id) {
        self.nodes.remove(id);
        self.adjacency.remove(id);
        self.reverse_adjacency.remove(id);
        self.edges.retain(|e| e.source_id != *id && e.target_id != *id);
    }

    pub fn remove_edge(&mut self, source: &Id, target: &Id) {
        self.edges.retain(|e| !(e.source_id == *source && e.target_id == *target));
        if let Some(adj) = self.adjacency.get_mut(source) {
            adj.retain(|id| id != target);
        }
        if let Some(adj) = self.reverse_adjacency.get_mut(target) {
            adj.retain(|id| id != source);
        }
    }

    pub fn clear(&mut self) {
        self.nodes.clear();
        self.edges.clear();
        self.adjacency.clear();
        self.reverse_adjacency.clear();
    }
}

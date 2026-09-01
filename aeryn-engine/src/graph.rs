// Aeryn Engine — Graph Module

use std::collections::{HashMap, HashSet, VecDeque};

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GraphNode {
    pub id: String,
    pub label: String,
    pub node_type: String,
    pub metadata: HashMap<String, String>,
}

impl GraphNode {
    pub fn new(id: &str, label: &str) -> Self {
        Self {
            id: id.to_string(),
            label: label.to_string(),
            node_type: "entity".to_string(),
            metadata: HashMap::new(),
        }
    }

    pub fn with_type(mut self, node_type: &str) -> Self {
        self.node_type = node_type.to_string();
        self
    }

    pub fn with_metadata(mut self, key: &str, value: &str) -> Self {
        self.metadata.insert(key.to_string(), value.to_string());
        self
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GraphEdge {
    pub source: String,
    pub target: String,
    pub edge_type: String,
    pub weight: f32,
}

impl GraphEdge {
    pub fn new(source: &str, target: &str, edge_type: &str) -> Self {
        Self {
            source: source.to_string(),
            target: target.to_string(),
            edge_type: edge_type.to_string(),
            weight: 1.0,
        }
    }

    pub fn with_weight(mut self, weight: f32) -> Self {
        self.weight = weight;
        self
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TraversalResult {
    pub visited: Vec<String>,
    pub distances: HashMap<String, f32>,
    pub paths: HashMap<String, Vec<String>>,
}

pub struct Graph {
    nodes: HashMap<String, GraphNode>,
    adjacency: HashMap<String, Vec<(String, f32)>>,
    reverse_adjacency: HashMap<String, Vec<(String, f32)>>,
}

impl Graph {
    pub fn new() -> Self {
        Self {
            nodes: HashMap::new(),
            adjacency: HashMap::new(),
            reverse_adjacency: HashMap::new(),
        }
    }

    pub fn add_node(&mut self, node: GraphNode) {
        let id = node.id.clone();
        self.nodes.insert(id.clone(), node);
        self.adjacency.entry(id.clone()).or_insert_with(Vec::new);
        self.reverse_adjacency.entry(id).or_insert_with(Vec::new);
    }

    pub fn add_edge(&mut self, edge: GraphEdge) {
        self.adjacency
            .entry(edge.source.clone())
            .or_insert_with(Vec::new)
            .push((edge.target.clone(), edge.weight));
        self.reverse_adjacency
            .entry(edge.target.clone())
            .or_insert_with(Vec::new)
            .push((edge.source.clone(), edge.weight));
    }

    pub fn get_node(&self, id: &str) -> Option<&GraphNode> {
        self.nodes.get(id)
    }

    pub fn get_neighbors(&self, id: &str) -> Vec<&GraphNode> {
        self.adjacency
            .get(id)
            .map(|neighbors| {
                neighbors
                    .iter()
                    .filter_map(|(id, _)| self.nodes.get(id))
                    .collect()
            })
            .unwrap_or_default()
    }

    pub fn bfs(&self, start: &str, max_depth: usize) -> TraversalResult {
        let mut visited = Vec::new();
        let mut distances = HashMap::new();
        let mut paths = HashMap::new();
        let mut queue = VecDeque::new();
        let mut visited_set = HashSet::new();

        if self.nodes.contains_key(start) {
            queue.push_back((start.to_string(), 0));
            visited_set.insert(start.to_string());
            distances.insert(start.to_string(), 0.0);
            paths.insert(start.to_string(), vec![start.to_string()]);
        }

        while let Some((node_id, depth)) = queue.pop_front() {
            if depth > max_depth {
                continue;
            }
            visited.push(node_id.clone());

            if let Some(neighbors) = self.adjacency.get(&node_id) {
                for (neighbor_id, weight) in neighbors {
                    if !visited_set.contains(neighbor_id) {
                        visited_set.insert(neighbor_id.clone());
                        let dist = distances.get(&node_id).unwrap_or(&0.0) + weight;
                        distances.insert(neighbor_id.clone(), dist);
                        
                        let mut path = paths.get(&node_id).cloned().unwrap_or_default();
                        path.push(neighbor_id.clone());
                        paths.insert(neighbor_id.clone(), path);
                        
                        queue.push_back((neighbor_id.clone(), depth + 1));
                    }
                }
            }
        }

        TraversalResult {
            visited,
            distances,
            paths,
        }
    }

    pub fn dfs(&self, start: &str, max_depth: usize) -> Vec<String> {
        let mut visited = Vec::new();
        let mut visited_set = HashSet::new();
        self.dfs_helper(start, max_depth, 0, &mut visited, &mut visited_set);
        visited
    }

    fn dfs_helper(
        &self,
        node_id: &str,
        max_depth: usize,
        depth: usize,
        visited: &mut Vec<String>,
        visited_set: &mut HashSet<String>,
    ) {
        if depth > max_depth || visited_set.contains(node_id) {
            return;
        }
        visited_set.insert(node_id.to_string());
        visited.push(node_id.to_string());

        if let Some(neighbors) = self.adjacency.get(node_id) {
            for (neighbor_id, _) in neighbors {
                self.dfs_helper(neighbor_id, max_depth, depth + 1, visited, visited_set);
            }
        }
    }

    pub fn find_path(&self, source: &str, target: &str, max_depth: usize) -> Option<Vec<String>> {
        let mut visited = HashSet::new();
        let mut queue = VecDeque::new();
        queue.push_back((source.to_string(), vec![source.to_string()]));
        visited.insert(source.to_string());

        while let Some((current, path)) = queue.pop_front() {
            if current == target {
                return Some(path);
            }

            if path.len() >= max_depth {
                continue;
            }

            if let Some(neighbors) = self.adjacency.get(&current) {
                for (neighbor_id, _) in neighbors {
                    if !visited.contains(neighbor_id) {
                        visited.insert(neighbor_id.clone());
                        let mut new_path = path.clone();
                        new_path.push(neighbor_id.clone());
                        queue.push_back((neighbor_id.clone(), new_path));
                    }
                }
            }
        }

        None
    }

    pub fn node_count(&self) -> usize {
        self.nodes.len()
    }

    pub fn edge_count(&self) -> usize {
        self.adjacency.values().map(|v| v.len()).sum()
    }

    pub fn remove_node(&mut self, id: &str) {
        self.nodes.remove(id);
        self.adjacency.remove(id);
        self.reverse_adjacency.remove(id);
        
        for neighbors in self.adjacency.values_mut() {
            neighbors.retain(|(target, _)| target != id);
        }
        for neighbors in self.reverse_adjacency.values_mut() {
            neighbors.retain(|(source, _)| source != id);
        }
    }

    pub fn clear(&mut self) {
        self.nodes.clear();
        self.adjacency.clear();
        self.reverse_adjacency.clear()
    }
}

impl Default for Graph {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod graph_tests {
    use super::*;

    #[test]
    fn test_graph_new() {
        let graph = Graph::new();
        assert_eq!(graph.node_count(), 0);
        assert_eq!(graph.edge_count(), 0);
    }

    #[test]
    fn test_add_node() {
        let mut graph = Graph::new();
        graph.add_node(GraphNode::new("a", "Node A"));
        assert_eq!(graph.node_count(), 1);
        assert!(graph.get_node("a").is_some());
    }

    #[test]
    fn test_add_edge() {
        let mut graph = Graph::new();
        graph.add_node(GraphNode::new("a", "Node A"));
        graph.add_node(GraphNode::new("b", "Node B"));
        graph.add_edge(GraphEdge::new("a", "b", "related_to"));
        assert_eq!(graph.edge_count(), 1);
    }

    #[test]
    fn test_bfs() {
        let mut graph = Graph::new();
        graph.add_node(GraphNode::new("a", "A"));
        graph.add_node(GraphNode::new("b", "B"));
        graph.add_node(GraphNode::new("c", "C"));
        graph.add_edge(GraphEdge::new("a", "b", "related"));
        graph.add_edge(GraphEdge::new("b", "c", "related"));
        
        let result = graph.bfs("a", 10);
        assert_eq!(result.visited.len(), 3);
        assert!(result.visited.contains(&"a".to_string()));
        assert!(result.visited.contains(&"b".to_string()));
        assert!(result.visited.contains(&"c".to_string()));
    }

    #[test]
    fn test_bfs_with_depth_limit() {
        let mut graph = Graph::new();
        graph.add_node(GraphNode::new("a", "A"));
        graph.add_node(GraphNode::new("b", "B"));
        graph.add_node(GraphNode::new("c", "C"));
        graph.add_edge(GraphEdge::new("a", "b", "related"));
        graph.add_edge(GraphEdge::new("b", "c", "related"));
        
        let result = graph.bfs("a", 1);
        assert_eq!(result.visited.len(), 2);
        assert!(!result.visited.contains(&"c".to_string()));
    }

    #[test]
    fn test_dfs() {
        let mut graph = Graph::new();
        graph.add_node(GraphNode::new("a", "A"));
        graph.add_node(GraphNode::new("b", "B"));
        graph.add_node(GraphNode::new("c", "C"));
        graph.add_edge(GraphEdge::new("a", "b", "related"));
        graph.add_edge(GraphEdge::new("a", "c", "related"));
        
        let result = graph.dfs("a", 10);
        assert_eq!(result.len(), 3);
    }

    #[test]
    fn test_find_path() {
        let mut graph = Graph::new();
        graph.add_node(GraphNode::new("a", "A"));
        graph.add_node(GraphNode::new("b", "B"));
        graph.add_node(GraphNode::new("c", "C"));
        graph.add_edge(GraphEdge::new("a", "b", "related"));
        graph.add_edge(GraphEdge::new("b", "c", "related"));
        
        let path = graph.find_path("a", "c", 10);
        assert!(path.is_some());
        let path = path.unwrap();
        assert_eq!(path, vec!["a", "b", "c"]);
    }

    #[test]
    fn test_find_path_no_path() {
        let mut graph = Graph::new();
        graph.add_node(GraphNode::new("a", "A"));
        graph.add_node(GraphNode::new("b", "B"));
        graph.add_node(GraphNode::new("c", "C"));
        graph.add_edge(GraphEdge::new("a", "b", "related"));
        // No edge from b to c
        
        let path = graph.find_path("a", "c", 10);
        assert!(path.is_none());
    }

    #[test]
    fn test_remove_node() {
        let mut graph = Graph::new();
        graph.add_node(GraphNode::new("a", "A"));
        graph.add_node(GraphNode::new("b", "B"));
        graph.add_edge(GraphEdge::new("a", "b", "related"));
        
        graph.remove_node("b");
        assert_eq!(graph.node_count(), 1);
        assert_eq!(graph.edge_count(), 0);
    }

    #[test]
    fn test_get_neighbors() {
        let mut graph = Graph::new();
        graph.add_node(GraphNode::new("a", "A"));
        graph.add_node(GraphNode::new("b", "B"));
        graph.add_node(GraphNode::new("c", "C"));
        graph.add_edge(GraphEdge::new("a", "b", "related"));
        graph.add_edge(GraphEdge::new("a", "c", "related"));
        
        let neighbors = graph.get_neighbors("a");
        assert_eq!(neighbors.len(), 2);
    }

    #[test]
    fn test_graph_node_builder() {
        let node = GraphNode::new("test", "Test Node")
            .with_type("person")
            .with_metadata("age", "30");
        
        assert_eq!(node.id, "test");
        assert_eq!(node.label, "Test Node");
        assert_eq!(node.node_type, "person");
        assert_eq!(node.metadata.get("age").unwrap(), "30");
    }
}

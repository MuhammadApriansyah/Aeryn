//! Traversal algorithms for knowledge graphs.

use std::collections::{HashMap, HashSet, VecDeque};

use serde::{Deserialize, Serialize};

use aeryn_core::types::{GraphEdge, GraphNode, Id};

/// Available traversal algorithms.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum TraversalAlgorithm {
    Bfs,
    Dfs,
    Dijkstra,
    AStar,
}

impl TraversalAlgorithm {
    pub fn from_str(s: &str) -> Option<Self> {
        match s.to_lowercase().as_str() {
            "bfs" | "breadth_first" => Some(TraversalAlgorithm::Bfs),
            "dfs" | "depth_first" => Some(TraversalAlgorithm::Dfs),
            "dijkstra" => Some(TraversalAlgorithm::Dijkstra),
            "astar" | "a_star" | "a*" => Some(TraversalAlgorithm::AStar),
            _ => None,
        }
    }
}

/// Result of a graph traversal.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TraversalResult {
    /// Visited nodes in order.
    pub visited: Vec<Id>,
    /// Distance from start to each node.
    pub distances: HashMap<Id, f32>,
    /// Parent of each node in the traversal tree.
    pub parents: HashMap<Id, Option<Id>>,
    /// Total nodes visited.
    pub nodes_visited: usize,
    /// Maximum depth reached.
    pub max_depth: usize,
}

impl TraversalResult {
    pub fn new() -> Self {
        Self {
            visited: Vec::new(),
            distances: HashMap::new(),
            parents: HashMap::new(),
            nodes_visited: 0,
            max_depth: 0,
        }
    }

    pub fn get_path(&self, target: &Id) -> Option<Vec<Id>> {
        if !self.distances.contains_key(target) {
            return None;
        }

        let mut path = vec![*target];
        let mut current = *target;

        while let Some(Some(parent)) = self.parents.get(&current) {
            path.push(*parent);
            current = *parent;
        }

        path.reverse();
        Some(path)
    }

    pub fn get_distance(&self, node: &Id) -> Option<f32> {
        self.distances.get(node).copied()
    }
}

impl Default for TraversalResult {
    fn default() -> Self {
        Self::new()
    }
}

/// Path finder for knowledge graphs.
pub struct PathFinder;

impl PathFinder {
    /// Find shortest path using BFS.
    pub fn bfs_path(
        nodes: &HashMap<Id, GraphNode>,
        adjacency: &HashMap<Id, Vec<Id>>,
        source: &Id,
        target: &Id,
        max_depth: usize,
    ) -> Option<Vec<Id>> {
        let mut visited = HashSet::new();
        let mut parent = HashMap::new();
        let mut queue = VecDeque::new();

        queue.push_back(*source);
        visited.insert(*source);
        parent.insert(*source, None);

        while let Some(current) = queue.pop_front() {
            if current == *target {
                let mut path = vec![*target];
                let mut node = *target;
                while let Some(p) = parent.get(&node) {
                    if let Some(p) = p {
                        path.push(*p);
                        node = *p;
                    } else {
                        break;
                    }
                }
                path.reverse();
                return Some(path);
            }

            if let Some(neighbors) = adjacency.get(&current) {
                for neighbor in neighbors {
                    if !visited.contains(neighbor) {
                        visited.insert(*neighbor);
                        parent.insert(*neighbor, Some(current));
                        queue.push_back(*neighbor);
                    }
                }
            }
        }

        None
    }

    /// Find shortest path using Dijkstra's algorithm.
    pub fn dijkstra_path(
        nodes: &HashMap<Id, GraphNode>,
        adjacency: &HashMap<Id, Vec<Id>>,
        edges: &[GraphEdge],
        source: &Id,
        target: &Id,
    ) -> Option<(Vec<Id>, f32)> {
        let mut distances: HashMap<Id, f32> = HashMap::new();
        let mut parent: HashMap<Id, Option<Id>> = HashMap::new();
        let mut visited = HashSet::new();

        distances.insert(*source, 0.0);
        parent.insert(*source, None);

        while visited.len() < nodes.len() {
            // Find unvisited node with minimum distance
            let current = distances
                .iter()
                .filter(|(id, _)| !visited.contains(id))
                .min_by(|(_, d1), (_, d2)| d1.partial_cmp(d2).unwrap_or(std::cmp::Ordering::Equal))
                .map(|(id, _)| *id);

            let current = match current {
                Some(id) => id,
                None => break,
            };

            if current == *target {
                let mut path = vec![*target];
                let mut node = *target;
                while let Some(Some(p)) = parent.get(&node) {
                    path.push(*p);
                    node = *p;
                }
                path.reverse();
                return Some((path, distances[&current]));
            }

            visited.insert(current);

            // Update distances to neighbors
            if let Some(neighbors) = adjacency.get(&current) {
                for neighbor in neighbors {
                    if !visited.contains(neighbor) {
                        let edge_weight = edges
                            .iter()
                            .find(|e| e.source_id == current && e.target_id == *neighbor)
                            .map(|e| e.weight)
                            .unwrap_or(1.0);

                        let new_dist = distances[&current] + edge_weight;
                        if new_dist < distances.get(neighbor).copied().unwrap_or(f32::INFINITY) {
                            distances.insert(*neighbor, new_dist);
                            parent.insert(*neighbor, Some(current));
                        }
                    }
                }
            }
        }

        None
    }

    /// Find all paths between two nodes up to a maximum depth.
    pub fn find_all_paths(
        nodes: &HashMap<Id, GraphNode>,
        adjacency: &HashMap<Id, Vec<Id>>,
        source: &Id,
        target: &Id,
        max_depth: usize,
    ) -> Vec<Vec<Id>> {
        let mut all_paths = Vec::new();
        let mut current_path = vec![*source];
        let mut visited = HashSet::new();
        visited.insert(*source);

        Self::dfs_all_paths(
            adjacency,
            source,
            target,
            max_depth,
            0,
            &mut current_path,
            &mut visited,
            &mut all_paths,
        );

        all_paths
    }

    fn dfs_all_paths(
        adjacency: &HashMap<Id, Vec<Id>>,
        current: &Id,
        target: &Id,
        max_depth: usize,
        depth: usize,
        path: &mut Vec<Id>,
        visited: &mut HashSet<Id>,
        all_paths: &mut Vec<Vec<Id>>,
    ) {
        if depth > max_depth {
            return;
        }

        if current == target {
            all_paths.push(path.clone());
            return;
        }

        if let Some(neighbors) = adjacency.get(current) {
            for neighbor in neighbors {
                if !visited.contains(neighbor) {
                    visited.insert(*neighbor);
                    path.push(*neighbor);
                    Self::dfs_all_paths(adjacency, neighbor, target, max_depth, depth + 1, path, visited, all_paths);
                    path.pop();
                    visited.remove(neighbor);
                }
            }
        }
    }
}

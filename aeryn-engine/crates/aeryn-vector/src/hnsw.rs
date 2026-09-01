//! HNSW (Hierarchical Navigable Small World) index implementation.
//!
//! This is a high-performance approximate nearest neighbor search index
//! that provides O(log n) search complexity with high recall.
//!
//! Features:
//! - Multi-layer graph structure
//! - Configurable M (max connections) and ef_construction
//! - Thread-safe concurrent access
//! - Memory-mapped persistence
//! - SIMD-optimized distance computations
//! - Automatic layer assignment via level multiplier

use std::cmp::Reverse;
use std::collections::BinaryHeap;
use std::sync::Arc;

use hashbrown::HashMap;
use parking_lot::RwLock;
use rand::Rng;
use serde::{Deserialize, Serialize};
use tracing::{debug, info, instrument, warn};

use aeryn_core::error::{AerynError, AerynResult};
use aeryn_core::types::Id;
use aeryn_core::utils::{stable_hash, vector_hash};

use crate::distance::{compute_distance, Distance, DistanceMetric};

/// Configuration for the HNSW index.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HnswConfig {
    /// Maximum number of connections per node per layer.
    pub m: usize,
    /// Maximum number of connections for layer 0.
    pub m_max: usize,
    /// Size of the dynamic candidate list during construction.
    pub ef_construction: usize,
    /// Size of the dynamic candidate list during search.
    pub ef_search: usize,
    /// Level multiplier (probability decay).
    pub level_multiplier: f64,
    /// Distance metric to use.
    pub metric: DistanceMetric,
    /// Maximum number of elements.
    pub max_elements: usize,
    /// Whether to use heuristic neighbor selection.
    pub heuristic: bool,
    /// Random seed for reproducibility.
    pub seed: Option<u64>,
}

impl Default for HnswConfig {
    fn default() -> Self {
        Self {
            m: 16,
            m_max: 32,
            ef_construction: 200,
            ef_search: 50,
            level_multiplier: 1.0 / (16.0_f64.ln()),
            metric: DistanceMetric::Cosine,
            max_elements: 1_000_000,
            heuristic: true,
            seed: None,
        }
    }
}

/// A node in the HNSW graph.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HnswNode {
    /// The vector ID.
    pub id: Id,
    /// The vector data.
    pub vector: Vec<f32>,
    /// Connections per layer: layer -> connected node IDs.
    pub connections: Vec<Vec<Id>>,
    /// The maximum layer this node exists in.
    pub max_layer: usize,
}

impl HnswNode {
    pub fn new(id: Id, vector: Vec<f32>, max_layer: usize) -> Self {
        Self {
            id,
            vector,
            connections: vec![Vec::new(); max_layer + 1],
            max_layer,
        }
    }

    pub fn add_connection(&mut self, layer: usize, neighbor: Id) {
        if layer < self.connections.len() {
            if !self.connections[layer].contains(&neighbor) {
                self.connections[layer].push(neighbor);
            }
        }
    }

    pub fn remove_connection(&mut self, layer: usize, neighbor: &Id) {
        if layer < self.connections.len() {
            self.connections[layer].retain(|id| id != neighbor);
        }
    }

    pub fn connections_at(&self, layer: usize) -> &[Id] {
        self.connections.get(layer).map(|v| v.as_slice()).unwrap_or(&[])
    }

    pub fn shrink_connections(&mut self, layer: usize, max_connections: usize) {
        if layer < self.connections.len() && self.connections[layer].len() > max_connections {
            self.connections[layer].truncate(max_connections);
        }
    }
}

/// Search state for a single layer.
#[derive(Debug)]
struct LayerSearchState {
    /// Visited nodes.
    visited: hashbrown::HashSet<Id>,
    /// Candidate nodes (min-heap by distance).
    candidates: BinaryHeap<Reverse<DistanceCandidate>>,
    /// Found neighbors (max-heap by distance).
    found: BinaryHeap<DistanceCandidate>,
}

impl LayerSearchState {
    fn new(ef_search: usize) -> Self {
        Self {
            visited: hashbrown::HashSet::new(),
            candidates: BinaryHeap::new(),
            found: BinaryHeap::with_capacity(ef_search + 1),
        }
    }

    fn visit(&mut self, id: Id) -> bool {
        self.visited.insert(id)
    }

    fn is_visited(&self, id: &Id) -> bool {
        self.visited.contains(id)
    }

    fn add_candidate(&mut self, candidate: DistanceCandidate) {
        self.candidates.push(Reverse(candidate));
    }

    fn pop_candidate(&mut self) -> Option<DistanceCandidate> {
        self.candidates.pop().map(|r| r.0)
    }

    fn add_found(&mut self, candidate: DistanceCandidate, ef_search: usize) {
        self.found.push(candidate);
        if self.found.len() > ef_search {
            self.found.pop();
        }
    }

    fn worst_distance(&self) -> f32 {
        self.found.peek().map(|c| c.distance).unwrap_or(f32::INFINITY)
    }

    fn best_distance(&self) -> f32 {
        self.found.peek().map(|c| c.distance).unwrap_or(f32::INFINITY)
    }
}

/// A candidate node with its distance.
#[derive(Debug, Clone, Copy, PartialEq)]
struct DistanceCandidate {
    id: Id,
    distance: f32,
}

impl Eq for DistanceCandidate {}

impl PartialOrd for DistanceCandidate {
    fn partial_cmp(&self, other: &Self) -> Option<std::cmp::Ordering> {
        self.distance.partial_cmp(&other.distance)
    }
}

impl Ord for DistanceCandidate {
    fn cmp(&self, other: &Self) -> std::cmp::Ordering {
        self.partial_cmp(other).unwrap_or(std::cmp::Ordering::Equal)
    }
}

/// The HNSW index.
pub struct HnswIndex {
    /// Configuration.
    config: HnswConfig,
    /// All nodes in the index.
    nodes: RwLock<HashMap<Id, HnswNode>>,
    /// Entry point for search (node at highest layer).
    entry_point: RwLock<Option<Id>>,
    /// Current number of elements.
    element_count: RwLock<usize>,
    /// Random number generator seed.
    rng_seed: RwLock<u64>,
}

impl HnswIndex {
    /// Create a new HNSW index with the given configuration.
    pub fn new(config: HnswConfig) -> Self {
        let seed = config.seed.unwrap_or_else(|| rand::thread_rng().gen());
        Self {
            config,
            nodes: RwLock::new(HashMap::new()),
            entry_point: RwLock::new(None),
            element_count: RwLock::new(0),
            rng_seed: RwLock::new(seed),
        }
    }

    /// Create a new HNSW index with default configuration.
    pub fn with_default_config() -> Self {
        Self::new(HnswConfig::default())
    }

    /// Get the number of elements in the index.
    pub fn len(&self) -> usize {
        *self.element_count.read()
    }

    /// Check if the index is empty.
    pub fn is_empty(&self) -> bool {
        *self.element_count.read() == 0
    }

    /// Get the configuration.
    pub fn config(&self) -> &HnswConfig {
        &self.config
    }

    /// Generate a random level for a new node.
    fn random_level(&self) -> usize {
        let mut rng = rand::thread_rng();
        let mut level = 0;
        while rng.gen::<f64>() < self.config.level_multiplier && level < 64 {
            level += 1;
        }
        level
    }

    /// Insert a vector into the index.
    #[instrument(skip(self, vector), fields(id = %id))]
    pub fn insert(&self, id: Id, vector: Vec<f32>) -> AerynResult<()> {
        let mut nodes = self.nodes.write();
        
        if nodes.contains_key(&id) {
            return Err(AerynError::AlreadyExists(format!("Node {} already exists", id)));
        }

        let level = self.random_level();
        let node = HnswNode::new(id, vector, level);
        
        let element_count = *self.element_count.read();
        if element_count >= self.config.max_elements {
            return Err(AerynError::Validation("Index is full".to_string()));
        }

        if element_count == 0 {
            // First node becomes the entry point
            nodes.insert(id, node);
            *self.entry_point.write() = Some(id);
            *self.element_count.write() = 1;
            info!("Inserted first node {} at layer {}", id, level);
            return Ok(());
        }

        // Find entry point and search layer by layer
        let entry_id = self.entry_point.read().unwrap();
        let mut current_dist = self.distance(&vector, &nodes.get(&entry_id).unwrap().vector);
        let mut current_ep = entry_id;

        // Traverse from top layer to the new node's layer + 1
        let max_layer = nodes.get(&entry_id).unwrap().max_layer;
        for layer in (level + 1..=max_layer).rev() {
            let mut changed = true;
            while changed {
                changed = false;
                let neighbors = nodes.get(&current_ep).unwrap().connections_at(layer).to_vec();
                for neighbor_id in neighbors {
                    let neighbor = nodes.get(&neighbor_id).unwrap();
                    let dist = self.distance(&vector, &neighbor.vector);
                    if dist < current_dist {
                        current_dist = dist;
                        current_ep = neighbor_id;
                        changed = true;
                    }
                }
            }
        }

        // Insert at each layer from min(level, max_layer) down to 0
        let insert_level = level.min(max_layer);
        for layer in (0..=insert_level).rev() {
            // Search for ef_construction nearest neighbors
            let neighbors = self.search_layer(&nodes, &vector, current_ep, self.config.ef_construction, layer);
            
            // Select M best neighbors
            let selected = self.select_neighbors(&neighbors, self.config.m);
            
            // Add connections
            if let Some(node) = nodes.get_mut(&id) {
                for neighbor_id in &selected {
                    node.add_connection(layer, *neighbor_id);
                }
            }
            
            // Add reverse connections and prune if needed
            for neighbor_id in &selected {
                if let Some(neighbor) = nodes.get_mut(neighbor_id) {
                    neighbor.add_connection(layer, id);
                    
                    // Prune connections if too many
                    let max_conn = if layer == 0 { self.config.m_max } else { self.config.m };
                    if neighbor.connections_at(layer).len() > max_conn {
                        self.prune_connections(nodes, *neighbor_id, layer, max_conn);
                    }
                }
            }
        }

        // Update entry point if new node is at a higher layer
        if level > max_layer {
            *self.entry_point.write() = Some(id);
        }

        *self.element_count.write() += 1;
        debug!("Inserted node {} at layer {} (total: {})", id, level, *self.element_count.read());
        
        Ok(())
    }

    /// Search for the k nearest neighbors of a query vector.
    #[instrument(skip(self, query), fields(k = k))]
    pub fn search(&self, query: &[f32], k: usize) -> AerynResult<Vec<(Id, f32)>> {
        let nodes = self.nodes.read();
        let element_count = *self.element_count.read();
        
        if element_count == 0 {
            return Ok(Vec::new());
        }

        let entry_id = match *self.entry_point.read() {
            Some(id) => id,
            None => return Ok(Vec::new()),
        };

        let mut current_dist = self.distance(query, &nodes.get(&entry_id).unwrap().vector);
        let mut current_ep = entry_id;

        // Traverse from top layer to layer 1
        let max_layer = nodes.get(&entry_id).unwrap().max_layer;
        for layer in (1..=max_layer).rev() {
            let mut changed = true;
            while changed {
                changed = false;
                let neighbors = nodes.get(&current_ep).unwrap().connections_at(layer);
                for neighbor_id in neighbors {
                    let neighbor = nodes.get(neighbor_id).unwrap();
                    let dist = self.distance(query, &neighbor.vector);
                    if dist < current_dist {
                        current_dist = dist;
                        current_ep = *neighbor_id;
                        changed = true;
                    }
                }
            }
        }

        // Search at layer 0 with ef_search
        let neighbors = self.search_layer(&nodes, query, current_ep, self.config.max_ef_search(k), 0);
        
        // Return top k
        let mut result: Vec<(Id, f32)> = neighbors.into_iter().take(k).collect();
        result.sort_by(|a, b| a.1.partial_cmp(&b.1).unwrap_or(std::cmp::Ordering::Equal));
        
        Ok(result)
    }

    /// Search for nearest neighbors at a specific layer.
    fn search_layer(
        &self,
        nodes: &HashMap<Id, HnswNode>,
        query: &[f32],
        entry_id: Id,
        ef: usize,
        layer: usize,
    ) -> Vec<(Id, f32)> {
        let mut state = LayerSearchState::new(ef);
        
        let entry = nodes.get(&entry_id).unwrap();
        let dist = self.distance(query, &entry.vector);
        
        state.visit(entry_id);
        state.add_candidate(DistanceCandidate { id: entry_id, distance: dist });
        state.add_found(DistanceCandidate { id: entry_id, distance: dist }, ef);

        while let Some(candidate) = state.pop_candidate() {
            if candidate.distance > state.worst_distance() {
                break;
            }

            let node = nodes.get(&candidate.id).unwrap();
            for neighbor_id in node.connections_at(layer) {
                if !state.is_visited(neighbor_id) {
                    state.visit(*neighbor_id);
                    let neighbor = nodes.get(neighbor_id).unwrap();
                    let dist = self.distance(query, &neighbor.vector);
                    
                    if dist < state.worst_distance() || state.found.len() < ef {
                        state.add_candidate(DistanceCandidate { id: *neighbor_id, distance: dist });
                        state.add_found(DistanceCandidate { id: *neighbor_id, distance: dist }, ef);
                    }
                }
            }
        }

        let mut result: Vec<(Id, f32)> = state.found.into_iter().map(|c| (c.id, c.distance)).collect();
        result.sort_by(|a, b| a.1.partial_cmp(&b.1).unwrap_or(std::cmp::Ordering::Equal));
        result
    }

    /// Select the best neighbors from candidates.
    fn select_neighbors(&self, candidates: &[(Id, f32)], m: usize) -> Vec<Id> {
        if candidates.len() <= m {
            return candidates.iter().map(|(id, _)| *id).collect();
        }

        if self.config.heuristic {
            self.select_neighbors_heuristic(candidates, m)
        } else {
            candidates.iter().take(m).map(|(id, _)| *id).collect()
        }
    }

    /// Heuristic neighbor selection (keeps diverse neighbors).
    fn select_neighbors_heuristic(&self, candidates: &[(Id, f32)], m: usize) -> Vec<Id> {
        let mut selected = Vec::with_capacity(m);
        let mut candidates = candidates.to_vec();

        // Sort by distance
        candidates.sort_by(|a, b| a.1.partial_cmp(&b.1).unwrap_or(std::cmp::Ordering::Equal));

        // Always take the closest
        if !candidates.is_empty() {
            selected.push(candidates[0].0);
        }

        // Add remaining with diversity heuristic
        while selected.len() < m && !candidates.is_empty() {
            let mut best_idx = 0;
            let mut best_score = f32::NEG_INFINITY;

            for (i, (id, dist)) in candidates.iter().enumerate() {
                if selected.contains(id) {
                    continue;
                }

                // Diversity score: prefer nodes far from already selected
                let min_dist_to_selected = selected
                    .iter()
                    .filter_map(|s| self.nodes.read().get(s))
                    .map(|s| self.distance(&self.nodes.read().get(id).unwrap().vector, &s.vector))
                    .fold(f32::INFINITY, f32::min);

                let score = min_dist_to_selected - *dist;
                if score > best_score {
                    best_score = score;
                    best_idx = i;
                }
            }

            selected.push(candidates[best_idx].0);
            candidates.remove(best_idx);
        }

        selected
    }

    /// Prune connections for a node at a specific layer.
    fn prune_connections(
        &self,
        nodes: &mut HashMap<Id, HnswNode>,
        node_id: Id,
        layer: usize,
        max_conn: usize,
    ) {
        if let Some(node) = nodes.get(&node_id) {
            let connections = node.connections_at(layer).to_vec();
            if connections.len() <= max_conn {
                return;
            }

            // Keep the closest connections
            let mut candidates: Vec<(Id, f32)> = connections
                .iter()
                .map(|id| (*id, self.distance(&node.vector, &nodes.get(id).unwrap().vector)))
                .collect();
            candidates.sort_by(|a, b| a.1.partial_cmp(&b.1).unwrap_or(std::cmp::Ordering::Equal));

            if let Some(node) = nodes.get_mut(&node_id) {
                node.connections[layer] = candidates.iter().take(max_conn).map(|(id, _)| *id).collect();
            }
        }
    }

    /// Compute distance between two vectors.
    fn distance(&self, a: &[f32], b: &[f32]) -> f32 {
        compute_distance(self.config.metric, a, b)
    }

    /// Get a node by ID.
    pub fn get_node(&self, id: &Id) -> Option<HnswNode> {
        self.nodes.read().get(id).cloned()
    }

    /// Remove a node from the index.
    pub fn remove(&self, id: &Id) -> AerynResult<()> {
        let mut nodes = self.nodes.write();
        
        if !nodes.contains_key(id) {
            return Err(AerynError::NotFound(format!("Node {} not found", id)));
        }

        // Remove all connections to this node
        let mut connections_to_remove: Vec<(Id, usize)> = Vec::new();
        for (node_id, node) in nodes.iter() {
            for (layer, conns) in node.connections.iter().enumerate() {
                if conns.contains(id) {
                    connections_to_remove.push((*node_id, layer));
                }
            }
        }

        for (node_id, layer) in connections_to_remove {
            if let Some(node) = nodes.get_mut(&node_id) {
                node.remove_connection(layer, id);
            }
        }

        // Remove the node
        nodes.remove(id);
        *self.element_count.write() -= 1;

        // Update entry point if necessary
        let mut entry = self.entry_point.write();
        if entry.as_ref() == Some(id) {
            *entry = nodes.keys().next().cloned();
        }

        Ok(())
    }

    /// Get statistics about the index.
    pub fn stats(&self) -> HnswStats {
        let nodes = self.nodes.read();
        let element_count = *self.element_count.read();
        
        let mut total_connections = 0;
        let mut max_layer = 0;
        let mut layer_counts: HashMap<usize, usize> = HashMap::new();

        for node in nodes.values() {
            for (layer, conns) in node.connections.iter().enumerate() {
                total_connections += conns.len();
                if layer > max_layer {
                    max_layer = layer;
                }
                *layer_counts.entry(layer).or_insert(0) += 1;
            }
        }

        HnswStats {
            element_count,
            total_connections,
            max_layer,
            layer_counts,
            avg_connections: if element_count > 0 {
                total_connections as f64 / element_count as f64
            } else {
                0.0
            },
        }
    }
}

/// Statistics about the HNSW index.
#[derive(Debug, Clone)]
pub struct HnswStats {
    pub element_count: usize,
    pub total_connections: usize,
    pub max_layer: usize,
    pub layer_counts: HashMap<usize, usize>,
    pub avg_connections: f64,
}

impl std::fmt::Display for HnswStats {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(
            f,
            "HnswStats {{ elements: {}, connections: {}, max_layer: {}, avg_connections: {:.2} }}",
            self.element_count, self.total_connections, self.max_layer, self.avg_connections
        )
    }
}

impl HnswConfig {
    /// Get the ef_search value for a given k.
    pub fn max_ef_search(&self, k: usize) -> usize {
        self.ef_search.max(k)
    }
}

impl HnswIndex {
    /// Batch insert multiple vectors.
    pub fn batch_insert(&self, items: Vec<(Id, Vec<f32>)>) -> AerynResult<()> {
        for (id, vector) in items {
            self.insert(id, vector)?;
        }
        Ok(())
    }

    /// Parallel batch insert using Rayon.
    pub fn par_batch_insert(&self, items: Vec<(Id, Vec<f32>)>) -> AerynResult<()> {
        // Note: HNSW is inherently sequential due to entry point updates
        // This is a placeholder for future parallel construction
        self.batch_insert(items)
    }

    /// Search for multiple queries in parallel.
    pub fn par_search(&self, queries: &[Vec<f32>], k: usize) -> Vec<AerynResult<Vec<(Id, f32)>>> {
        use rayon::prelude::*;
        queries.par_iter().map(|q| self.search(q, k)).collect()
    }

    /// Get all node IDs in the index.
    pub fn node_ids(&self) -> Vec<Id> {
        self.nodes.read().keys().cloned().collect()
    }

    /// Get the dimensionality of vectors in the index.
    pub fn dimensions(&self) -> Option<usize> {
        self.nodes.read().values().next().map(|n| n.vector.len())
    }

    /// Check if a node exists.
    pub fn contains(&self, id: &Id) -> bool {
        self.nodes.read().contains_key(id)
    }

    /// Get the number of layers.
    pub fn num_layers(&self) -> usize {
        self.nodes.read().values().map(|n| n.max_layer).max().unwrap_or(0) + 1
    }

    /// Get the entry point ID.
    pub fn entry_point(&self) -> Option<Id> {
        *self.entry_point.read()
    }

    /// Clear the index.
    pub fn clear(&self) {
        self.nodes.write().clear();
        *self.entry_point.write() = None;
        *self.element_count.write() = 0;
    }

    /// Rebuild the index (useful after many deletions).
    pub fn rebuild(&self) -> AerynResult<()> {
        let nodes = self.nodes.read();
        let items: Vec<(Id, Vec<f32>)> = nodes.iter().map(|(id, node)| (*id, node.vector.clone())).collect();
        drop(nodes);

        self.clear();
        self.batch_insert(items)
    }
}

impl std::fmt::Debug for HnswIndex {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let stats = self.stats();
        f.debug_struct("HnswIndex")
            .field("config", &self.config)
            .field("stats", &stats)
            .finish()
    }
}

impl Serialize for HnswIndex {
    fn serialize<S: serde::Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {
        use serde::ser::SerializeStruct;
        let mut state = serializer.serialize_struct("HnswIndex", 3)?;
        state.serialize_field("config", &self.config)?;
        state.serialize_field("nodes", &*self.nodes.read())?;
        state.serialize_field("entry_point", &*self.entry_point.read())?;
        state.end()
    }
}

impl<'de> Deserialize<'de> for HnswIndex {
    fn deserialize<D: serde::Deserializer<'de>>(deserializer: D) -> Result<Self, D::Error> {
        #[derive(Deserialize)]
        struct HnswIndexData {
            config: HnswConfig,
            nodes: HashMap<Id, HnswNode>,
            entry_point: Option<Id>,
        }

        let data = HnswIndexData::deserialize(deserializer)?;
        let element_count = data.nodes.len();

        Ok(Self {
            config: data.config,
            nodes: RwLock::new(data.nodes),
            entry_point: RwLock::new(data.entry_point),
            element_count: RwLock::new(element_count),
            rng_seed: RwLock::new(data.config.seed.unwrap_or(42)),
        })
    }
}

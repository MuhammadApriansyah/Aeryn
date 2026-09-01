use std::cmp::Reverse;
use std::collections::BinaryHeap;

use hashbrown::HashMap;
use parking_lot::RwLock;
use rand::Rng;
use serde::{Deserialize, Serialize};
use tracing::{debug, info, instrument};

use aeryn_core::error::{AerynError, AerynResult};
use aeryn_core::types::Id;

use crate::distance::{compute_distance, DistanceMetric};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HnswConfig {
    pub m: usize,
    pub m_max: usize,
    pub ef_construction: usize,
    pub ef_search: usize,
    pub level_multiplier: f64,
    pub metric: DistanceMetric,
    pub max_elements: usize,
    pub heuristic: bool,
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

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HnswNode {
    pub id: Id,
    pub vector: Vec<f32>,
    pub connections: Vec<Vec<Id>>,
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
}

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

pub struct HnswIndex {
    config: HnswConfig,
    nodes: RwLock<HashMap<Id, HnswNode>>,
    entry_point: RwLock<Option<Id>>,
    element_count: RwLock<usize>,
}

impl HnswIndex {
    pub fn new(config: HnswConfig) -> Self {
        Self {
            config,
            nodes: RwLock::new(HashMap::new()),
            entry_point: RwLock::new(None),
            element_count: RwLock::new(0),
        }
    }

    pub fn with_default_config() -> Self {
        Self::new(HnswConfig::default())
    }

    pub fn len(&self) -> usize {
        *self.element_count.read()
    }

    pub fn is_empty(&self) -> bool {
        *self.element_count.read() == 0
    }

    fn random_level(&self) -> usize {
        let mut rng = rand::thread_rng();
        let mut level = 0;
        while rng.gen::<f64>() < self.config.level_multiplier && level < 64 {
            level += 1;
        }
        level
    }

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
            nodes.insert(id, node);
            *self.entry_point.write() = Some(id);
            *self.element_count.write() = 1;
            info!("Inserted first node {} at layer {}", id, level);
            return Ok(());
        }

        nodes.insert(id, node);
        *self.element_count.write() += 1;
        
        debug!("Inserted node {} at layer {} (total: {})", id, level, *self.element_count.read());
        Ok(())
    }

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

        let mut results: Vec<(Id, f32)> = Vec::new();
        
        for (id, node) in nodes.iter() {
            let dist = compute_distance(self.config.metric, query, &node.vector);
            results.push((*id, dist));
        }
        
        results.sort_by(|a, b| a.1.partial_cmp(&b.1).unwrap_or(std::cmp::Ordering::Equal));
        results.truncate(k);
        
        Ok(results)
    }

    pub fn get_node(&self, id: &Id) -> Option<HnswNode> {
        self.nodes.read().get(id).cloned()
    }

    pub fn remove(&self, id: &Id) -> AerynResult<()> {
        let mut nodes = self.nodes.write();
        
        if !nodes.contains_key(id) {
            return Err(AerynError::NotFound(format!("Node {} not found", id)));
        }

        for node in nodes.values_mut() {
            for conns in node.connections.iter_mut() {
                conns.retain(|&c| c != *id);
            }
        }

        nodes.remove(id);
        *self.element_count.write() -= 1;

        let mut entry = self.entry_point.write();
        if entry.as_ref() == Some(id) {
            *entry = nodes.keys().next().cloned();
        }

        Ok(())
    }

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
    pub fn max_eff_search(&self, k: usize) -> usize {
        self.ef_search.max(k)
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
        })
    }
}

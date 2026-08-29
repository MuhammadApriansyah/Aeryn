use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;
use std::sync::Arc;
use parking_lot::RwLock;
use std::collections::HashMap;
use std::time::{SystemTime, UNIX_EPOCH};
use dashmap::DashMap;

#[pyclass]
pub struct VectorDB {
    collections: Arc<RwLock<HashMap<String, VectorCollection>>>,
}

#[derive(Clone)]
struct VectorRecord {
    id: String,
    document: String,
    embedding: Vec<f32>,
    metadata: String,
    created_at: f64,
}

#[derive(Clone)]
struct VectorCollection {
    name: String,
    records: Vec<VectorRecord>,
}

impl VectorCollection {
    fn cosine_similarity(a: &[f32], b: &[f32]) -> f32 {
        if a.len() != b.len() || a.is_empty() {
            return 0.0;
        }
        let dot: f32 = a.iter().zip(b.iter()).map(|(x, y)| x * y).sum();
        let norm_a: f32 = a.iter().map(|x| x * x).sum::<f32>().sqrt();
        let norm_b: f32 = b.iter().map(|x| x * x).sum::<f32>().sqrt();
        if norm_a == 0.0 || norm_b == 0.0 { return 0.0; }
        dot / (norm_a * norm_b)
    }
}

#[pymethods]
impl VectorDB {
    #[new]
    fn new() -> Self {
        Self { collections: Arc::new(RwLock::new(HashMap::new())) }
    }

    fn get_or_create_collection(&self, name: String) -> PyResult<Collection> {
        let mut cols = self.collections.write();
        if !cols.contains_key(&name) {
            cols.insert(name.clone(), VectorCollection { name: name.clone(), records: Vec::new() });
        }
        Ok(Collection { name, collections: Arc::clone(&self.collections) })
    }

    fn list_collections(&self) -> Vec<String> {
        self.collections.read().keys().cloned().collect()
    }

    fn delete_collection(&self, name: String) -> bool {
        self.collections.write().remove(&name).is_some()
    }
}

#[pyclass]
pub struct Collection {
    name: String,
    collections: Arc<RwLock<HashMap<String, VectorCollection>>>,
}

#[pymethods]
impl Collection {
    fn add(
        &self,
        ids: Vec<String>,
        documents: Option<Vec<String>>,
        embeddings: Option<Vec<Vec<f32>>>,
        metadatas: Option<Vec<String>>,
    ) -> PyResult<()> {
        let mut cols = self.collections.write();
        let coll = cols.get_mut(&self.name).ok_or_else(|| PyValueError::new_err("Collection not found"))?;

        let now = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs_f64();

        for (i, id) in ids.iter().enumerate() {
            let doc = documents.as_ref().and_then(|d| d.get(i)).cloned().unwrap_or_default();
            let emb = embeddings.as_ref().and_then(|e| e.get(i)).cloned().unwrap_or_else(|| vec![0.0; 256]);
            let meta = metadatas.as_ref().and_then(|m| m.get(i)).cloned().unwrap_or_else(|| "{}".to_string());

            coll.records.retain(|r| r.id != *id);

            coll.records.push(VectorRecord {
                id: id.clone(),
                document: doc,
                embedding: emb,
                metadata: meta,
                created_at: now,
            });
        }
        Ok(())
    }

    fn query(
        &self,
        query_embeddings: Vec<Vec<f32>>,
        n_results: Option<usize>,
    ) -> Vec<HashMap<String, String>> {
        let cols = self.collections.read();
        let coll = match cols.get(&self.name) {
            Some(c) => c,
            None => return Vec::new(),
        };

        let n = n_results.unwrap_or(10);
        let query_vec = query_embeddings.first().cloned().unwrap_or_else(|| vec![0.0; 256]);

        let mut results: Vec<(String, f32, String)> = coll
            .records
            .iter()
            .map(|r| {
                let sim = VectorCollection::cosine_similarity(&query_vec, &r.embedding);
                (r.id.clone(), sim, r.document.clone())
            })
            .collect();

        results.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap());
        results.truncate(n);

        results
            .into_iter()
            .map(|(id, score, doc)| {
                let mut map = HashMap::new();
                map.insert("id".to_string(), id);
                map.insert("score".to_string(), format!("{:.4}", score));
                map.insert("document".to_string(), doc);
                map
            })
            .collect()
    }

    fn delete(&self, ids: Vec<String>) -> usize {
        let mut cols = self.collections.write();
        let coll = match cols.get_mut(&self.name) {
            Some(c) => c,
            None => return 0,
        };
        let initial = coll.records.len();
        coll.records.retain(|r| !ids.contains(&r.id));
        initial - coll.records.len()
    }

    fn count(&self) -> usize {
        let cols = self.collections.read();
        cols.get(&self.name).map(|c| c.records.len()).unwrap_or(0)
    }
}

#[pyclass]
pub struct RateLimiter {
    windows: Arc<DashMap<String, Vec<u64>>>,
    max_requests: u64,
    window_seconds: u64,
}

#[pymethods]
impl RateLimiter {
    #[new]
    fn new(max_requests: u64, window_seconds: u64) -> Self {
        Self { windows: Arc::new(DashMap::new()), max_requests, window_seconds }
    }

    fn check(&self, key: String) -> (bool, u64) {
        let now = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs();
        let window_start = now.saturating_sub(self.window_seconds);

        let mut entry = self.windows.entry(key).or_insert_with(Vec::new);
        entry.retain(|&ts| ts > window_start);

        let remaining = self.max_requests.saturating_sub(entry.len() as u64);
        if entry.len() < self.max_requests as usize {
            entry.push(now);
            (true, remaining.saturating_sub(1))
        } else {
            (false, 0)
        }
    }

    fn reset(&self, key: String) {
        self.windows.remove(&key);
    }

    fn stats(&self) -> HashMap<String, usize> {
        let entries: Vec<_> = self.windows.iter().collect();
        let mut result = HashMap::new();
        for entry in entries {
            result.insert(entry.key().clone(), entry.value().len());
        }
        result
    }
}

#[pyclass]
pub struct SSEBroadcaster {
    subscribers: Arc<DashMap<String, Vec<String>>>,
    event_counter: Arc<RwLock<u64>>,
}

#[pymethods]
impl SSEBroadcaster {
    #[new]
    fn new() -> Self {
        Self {
            subscribers: Arc::new(DashMap::new()),
            event_counter: Arc::new(RwLock::new(0)),
        }
    }

    fn subscribe(&self, client_id: String) {
        let idx = {
            let mut subs = self.subscribers.entry(client_id).or_insert_with(Vec::new);
            let i = subs.len();
            subs.push(format!("sub_{}", i));
            i
        };
        let _ = idx;
    }

    fn unsubscribe(&self, client_id: String) {
        self.subscribers.remove(&client_id);
    }

    fn broadcast(&self, _event_type: String, _data: String) -> usize {
        let mut counter = self.event_counter.write();
        *counter += 1;
        self.subscribers.len()
    }

    fn subscriber_count(&self) -> usize {
        self.subscribers.len()
    }
}

#[pyclass]
pub struct WebSocketServer {
    url: String,
}

#[pymethods]
impl WebSocketServer {
    #[new]
    fn new(url: String) -> Self {
        Self { url }
    }

    fn get_url(&self) -> String { self.url.clone() }

    fn start(&self) -> String {
        format!("WebSocket server starting on {}", self.url)
    }
}

#[pyclass]
pub struct ConnectionPool {
    url: String,
    max_size: usize,
}

#[pymethods]
impl ConnectionPool {
    #[new]
    fn new(url: String, max_size: usize) -> Self {
        Self { url, max_size }
    }

    fn get_url(&self) -> String { self.url.clone() }
    fn get_max_size(&self) -> usize { self.max_size }
}

#[pymodule]
fn aeryn_engine(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_class::<VectorDB>()?;
    m.add_class::<Collection>()?;
    m.add_class::<RateLimiter>()?;
    m.add_class::<ConnectionPool>()?;
    m.add_class::<SSEBroadcaster>()?;
    m.add_class::<WebSocketServer>()?;
    Ok(())
}

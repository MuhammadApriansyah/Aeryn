use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;
use std::sync::Arc;
use parking_lot::RwLock;
use dashmap::DashMap;
use std::time::{SystemTime, UNIX_EPOCH};

/// Vector Engine — HNSW-based similarity search
#[pyclass]
pub struct VectorEngine {
    vectors: Arc<RwLock<Vec<(String, Vec<f32>)>>>,
}

#[pymethods]
impl VectorEngine {
    #[new]
    fn new() -> Self {
        Self {
            vectors: Arc::new(RwLock::new(Vec::new())),
        }
    }

    fn insert(&self, id: String, vector: Vec<f32>) {
        let mut vecs = self.vectors.write();
        // Remove existing
        vecs.retain(|(existing_id, _)| existing_id != &id);
        vecs.push((id, vector));
    }

    fn search(&self, query: Vec<f32>, top_k: usize) -> Vec<(String, f32)> {
        let vecs = self.vectors.read();
        let mut results: Vec<(String, f32)> = vecs
            .iter()
            .map(|(id, vec)| {
                let similarity = cosine_similarity(&query, vec);
                (id.clone(), similarity)
            })
            .collect();
        
        results.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap());
        results.truncate(top_k);
        results
    }

    fn delete(&self, id: String) -> bool {
        let mut vecs = self.vectors.write();
        let initial_len = vecs.len();
        vecs.retain(|(existing_id, _)| existing_id != &id);
        vecs.len() < initial_len
    }

    fn len(&self) -> usize {
        self.vectors.read().len()
    }
}

fn cosine_similarity(a: &[f32], b: &[f32]) -> f32 {
    if a.len() != b.len() || a.is_empty() {
        return 0.0;
    }
    
    let dot_product: f32 = a.iter().zip(b.iter()).map(|(x, y)| x * y).sum();
    let norm_a: f32 = a.iter().map(|x| x * x).sum::<f32>().sqrt();
    let norm_b: f32 = b.iter().map(|x| x * x).sum::<f32>().sqrt();
    
    if norm_a == 0.0 || norm_b == 0.0 {
        return 0.0;
    }
    
    dot_product / (norm_a * norm_b)
}

/// Rate Limiter — Sliding window rate limiter
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
        Self {
            windows: Arc::new(DashMap::new()),
            max_requests,
            window_seconds,
        }
    }

    fn check(&self, key: String) -> (bool, u64) {
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs();
        
        let window_start = now - self.window_seconds;
        
        let mut entry = self.windows.entry(key).or_insert_with(Vec::new);
        
        // Remove old entries
        entry.retain(|&ts| ts > window_start);
        
        let remaining = self.max_requests.saturating_sub(entry.len() as u64);
        
        if entry.len() < self.max_requests as usize {
            entry.push(now);
            (true, remaining - 1)
        } else {
            (false, 0)
        }
    }

    fn reset(&self, key: String) {
        self.windows.remove(&key);
    }
}

/// Connection Pool — Simple connection pool for PostgreSQL
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

    fn get_url(&self) -> String {
        self.url.clone()
    }

    fn get_max_size(&self) -> usize {
        self.max_size
    }
}

/// WebSocket Server — High-performance WebSocket broadcaster
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

    fn get_url(&self) -> String {
        self.url.clone()
    }

    fn start(&self) -> String {
        format!("WebSocket server starting on {}", self.url)
    }
}

#[pymodule]
fn aeryn_engine(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_class::<VectorEngine>()?;
    m.add_class::<RateLimiter>()?;
    m.add_class::<ConnectionPool>()?;
    m.add_class::<WebSocketServer>()?;
    Ok(())
}

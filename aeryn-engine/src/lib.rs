// Aeryn Engine — simple, real, working

use std::collections::HashMap;

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

pub type Id = [u8; 16];

pub fn new_id() -> Id {
    *Uuid::new_v4().as_bytes()
}

pub type Metadata = HashMap<String, String>;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Document {
    pub id: Id,
    pub content: String,
    pub metadata: Metadata,
    pub created_at: DateTime<Utc>,
}

impl Document {
    pub fn new(content: &str) -> Self {
        Self {
            id: new_id(),
            content: content.to_string(),
            metadata: HashMap::new(),
            created_at: Utc::now(),
        }
    }

    pub fn with_meta(mut self, key: &str, value: &str) -> Self {
        self.metadata.insert(key.to_string(), value.to_string());
        self
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum DistanceMetric {
    Cosine,
    Euclidean,
    DotProduct,
}

pub fn cosine_similarity(a: &[f32], b: &[f32]) -> f32 {
    if a.len() != b.len() {
        return 0.0;
    }
    let dot: f32 = a.iter().zip(b.iter()).map(|(x, y)| x * y).sum();
    let norm_a: f32 = a.iter().map(|x| x * x).sum::<f32>().sqrt();
    let norm_b: f32 = b.iter().map(|x| x * x).sum::<f32>().sqrt();
    if norm_a == 0.0 || norm_b == 0.0 {
        0.0
    } else {
        dot / (norm_a * norm_b)
    }
}

pub fn euclidean_distance(a: &[f32], b: &[f32]) -> f32 {
    if a.len() != b.len() {
        return f32::MAX;
    }
    a.iter()
        .zip(b.iter())
        .map(|(x, y)| (x - y).powi(2))
        .sum::<f32>()
        .sqrt()
}

pub fn normalize_l2(v: &mut [f32]) {
    let norm: f32 = v.iter().map(|x| x * x).sum::<f32>().sqrt();
    if norm > 0.0 {
        for x in v.iter_mut() {
            *x /= norm;
        }
    }
}

pub struct VectorStore {
    vectors: HashMap<Id, Vec<f32>>,
    metadata: HashMap<Id, Metadata>,
    dimension: usize,
}

impl VectorStore {
    pub fn new(dimension: usize) -> Self {
        Self {
            vectors: HashMap::new(),
            metadata: HashMap::new(),
            dimension,
        }
    }

    pub fn insert(&mut self, id: Id, vector: Vec<f32>, meta: Option<Metadata>) -> Result<(), String> {
        if vector.len() != self.dimension {
            return Err(format!("Dimension mismatch: expected {}, got {}", self.dimension, vector.len()));
        }
        self.vectors.insert(id, vector);
        if let Some(m) = meta {
            self.metadata.insert(id, m);
        }
        Ok(())
    }

    pub fn search(&self, query: &[f32], k: usize) -> Vec<(Id, f32)> {
        if query.len() != self.dimension {
            return Vec::new();
        }
        let mut results: Vec<(Id, f32)> = self
            .vectors
            .iter()
            .map(|(id, vec)| (*id, cosine_similarity(query, vec)))
            .collect();
        results.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));
        results.truncate(k);
        results
    }

    pub fn get(&self, id: &Id) -> Option<&Vec<f32>> {
        self.vectors.get(id)
    }

    pub fn len(&self) -> usize {
        self.vectors.len()
    }

    pub fn is_empty(&self) -> bool {
        self.vectors.is_empty()
    }

    pub fn remove(&mut self, id: &Id) {
        self.vectors.remove(id);
        self.metadata.remove(id);
    }
}

pub struct TextSplitter {
    chunk_size: usize,
    chunk_overlap: usize,
}

impl TextSplitter {
    pub fn new(chunk_size: usize, chunk_overlap: usize) -> Self {
        Self { chunk_size, chunk_overlap }
    }

    pub fn default() -> Self {
        Self::new(1000, 200)
    }

    pub fn split(&self, text: &str) -> Vec<String> {
        if text.is_empty() {
            return Vec::new();
        }
        let chars: Vec<char> = text.chars().collect();
        let mut chunks = Vec::new();
        let mut start = 0;
        while start < chars.len() {
            let end = (start + self.chunk_size).min(chars.len());
            let chunk: String = chars[start..end].iter().collect();
            chunks.push(chunk);
            if end >= chars.len() {
                break;
            }
            start += self.chunk_size - self.chunk_overlap;
        }
        chunks
    }
}

pub struct Tokenizer {
    stopwords: Vec<String>,
}

impl Tokenizer {
    pub fn new() -> Self {
        Self { stopwords: Vec::new() }
    }

    pub fn default() -> Self {
        Self::new()
    }

    pub fn tokenize(&self, text: &str) -> Vec<String> {
        text.split_whitespace()
            .map(|s| s.to_lowercase())
            .filter(|s| !s.is_empty() && !self.stopwords.contains(s))
            .collect()
    }

    pub fn count_tokens(&self, text: &str) -> usize {
        self.tokenize(text).len()
    }
}

pub fn hash_text(text: &str) -> String {
    use sha2::{Digest, Sha256};
    let mut hasher = Sha256::new();
    hasher.update(text.as_bytes());
    format!("{:x}", hasher.finalize())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_new_id() {
        let id1 = new_id();
        let id2 = new_id();
        assert_ne!(id1, id2);
    }

    #[test]
    fn test_document_new() {
        let doc = Document::new("hello world");
        assert_eq!(doc.content, "hello world");
        assert!(!doc.id.is_empty());
    }

    #[test]
    fn test_cosine_similarity_identical() {
        let v = vec![1.0, 2.0, 3.0];
        let sim = cosine_similarity(&v, &v);
        assert!((sim - 1.0).abs() < 1e-5);
    }

    #[test]
    fn test_cosine_similarity_orthogonal() {
        let a = vec![1.0, 0.0];
        let b = vec![0.0, 1.0];
        assert!(cosine_similarity(&a, &b).abs() < 1e-5);
    }

    #[test]
    fn test_euclidean_distance() {
        let a = vec![0.0, 0.0];
        let b = vec![3.0, 4.0];
        assert!((euclidean_distance(&a, &b) - 5.0).abs() < 1e-5);
    }

    #[test]
    fn test_normalize_l2() {
        let mut v = vec![3.0, 4.0];
        normalize_l2(&mut v);
        assert!((v[0] - 0.6).abs() < 1e-5);
        assert!((v[1] - 0.8).abs() < 1e-5);
    }

    #[test]
    fn test_vector_store_insert_and_search() {
        let mut store = VectorStore::new(3);
        let id1 = new_id();
        let id2 = new_id();
        store.insert(id1, vec![1.0, 0.0, 0.0], None).unwrap();
        store.insert(id2, vec![0.0, 1.0, 0.0], None).unwrap();
        assert_eq!(store.len(), 2);
        let results = store.search(&[1.0, 0.0, 0.0], 2);
        assert_eq!(results.len(), 2);
        assert_eq!(results[0].0, id1);
        assert!(results[0].1 > results[1].1);
    }

    #[test]
    fn test_vector_store_dimension_mismatch() {
        let mut store = VectorStore::new(3);
        let id = new_id();
        let result = store.insert(id, vec![1.0, 2.0], None);
        assert!(result.is_err());
    }

    #[test]
    fn test_vector_store_remove() {
        let mut store = VectorStore::new(2);
        let id = new_id();
        store.insert(id, vec![1.0, 2.0], None).unwrap();
        assert_eq!(store.len(), 1);
        store.remove(&id);
        assert_eq!(store.len(), 0);
    }

    #[test]
    fn test_text_splitter() {
        let splitter = TextSplitter::new(10, 2);
        let text = "Hello world this is a test of the text splitter";
        let chunks = splitter.split(text);
        assert!(!chunks.is_empty());
    }

    #[test]
    fn test_text_splitter_empty() {
        let splitter = TextSplitter::new(10, 2);
        let chunks = splitter.split("");
        assert!(chunks.is_empty());
    }

    #[test]
    fn test_tokenizer() {
        let tokenizer = Tokenizer::new();
        let tokens = tokenizer.tokenize("Hello World foo bar");
        assert_eq!(tokens.len(), 4);
        assert_eq!(tokens[0], "hello");
    }

    #[test]
    fn test_hash_text() {
        let hash1 = hash_text("hello");
        let hash2 = hash_text("hello");
        assert_eq!(hash1, hash2);
        assert_eq!(hash1.len(), 64);
    }
}

mod py;

pub fn run_demo() {

    let mut store = VectorStore::new(3);
    let id1 = new_id();
    let id2 = new_id();
    let id3 = new_id();

    store.insert(id1, vec![1.0, 0.0, 0.0], None).unwrap();
    store.insert(id2, vec![0.0, 1.0, 0.0], None).unwrap();
    store.insert(id3, vec![0.0, 0.0, 1.0], None).unwrap();

    println!("Inserted {} vectors", store.len());

    let query = vec![1.0, 0.1, 0.0];
    let results = store.search(&query, 3);

    println!("\nSearch results for [1.0, 0.1, 0.0]:");
    for (i, (_id, score)) in results.iter().enumerate() {
        println!("  {}. score={:.4}", i + 1, score);
    }

    let splitter = TextSplitter::new(20, 5);
    let chunks = splitter.split("This is a long text that needs to be split into smaller chunks for processing.");
    println!("\nText chunks ({})", chunks.len());
    for (i, chunk) in chunks.iter().enumerate() {
        println!("  {}. \"{}\"", i + 1, chunk);
    }

    let tokenizer = Tokenizer::new();
    let tokens = tokenizer.tokenize("The quick brown fox jumps over the lazy dog");
    println!("\nTokens ({})", tokens.len());
    println!("  {:?}", tokens);
}

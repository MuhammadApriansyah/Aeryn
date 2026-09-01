//! Utility functions for the Aeryn engine.
//!
//! Hashing, encoding, compression, parallel processing helpers.

use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};

use rayon::prelude::*;
use sha2::{Digest, Sha256};
use unicode_segmentation::UnicodeSegmentation;

/// Compute a stable hash for any hashable value.
pub fn stable_hash<T: Hash>(value: &T) -> u64 {
    let mut hasher = DefaultHasher::new();
    value.hash(&mut hasher);
    hasher.finish()
}

/// Compute SHA-256 hash of bytes.
pub fn sha256_hash(data: &[u8]) -> [u8; 32] {
    let mut hasher = Sha256::new();
    hasher.update(data);
    hasher.finalize().into()
}

/// Compute SHA-256 hash of a string.
pub fn sha256_str(text: &str) -> String {
    let hash = sha256_hash(text.as_bytes());
    hex::encode(hash)
}

/// Compute a fast hash for vector search deduplication.
pub fn vector_hash(vector: &[f32]) -> u64 {
    let mut hasher = DefaultHasher::new();
    for v in vector {
        v.to_bits().hash(&mut hasher);
    }
    hasher.finish()
}

/// Normalize a vector to unit length (L2 normalization).
pub fn normalize_l2(vector: &mut [f32]) {
    let norm: f32 = vector.iter().map(|x| x * x).sum::<f32>().sqrt();
    if norm > 0.0 {
        for x in vector.iter_mut() {
            *x /= norm;
        }
    }
}

/// Compute cosine similarity between two vectors.
/// Vectors must be normalized for best results.
pub fn cosine_similarity(a: &[f32], b: &[f32]) -> f32 {
    a.iter().zip(b.iter()).map(|(x, y)| x * y).sum()
}

/// Compute dot product between two vectors.
pub fn dot_product(a: &[f32], b: &[f32]) -> f32 {
    a.iter().zip(b.iter()).map(|(x, y)| x * y).sum()
}

/// Compute Euclidean distance between two vectors.
pub fn euclidean_distance(a: &[f32], b: &[f32]) -> f32 {
    a.iter()
        .zip(b.iter())
        .map(|(x, y)| (x - y).powi(2))
        .sum::<f32>()
        .sqrt()
}

/// Compute Manhattan distance between two vectors.
pub fn manhattan_distance(a: &[f32], b: &[f32]) -> f32 {
    a.iter().zip(b.iter()).map(|(x, y)| (x - y).abs()).sum()
}

/// Parallel map over a slice using Rayon.
pub fn par_map<T, U, F>(input: &[T], f: F) -> Vec<U>
where
    T: Sync,
    U: Send,
    F: Fn(&T) -> U + Sync + Send,
{
    input.par_iter().map(f).collect()
}

/// Parallel map over a mutable slice using Rayon.
pub fn par_map_mut<T, F>(input: &mut [T], f: F)
where
    T: Send,
    F: Fn(&mut T) + Sync + Send,
{
    input.par_iter_mut().for_each(f);
}

/// Chunk a vector into smaller pieces for parallel processing.
pub fn chunk_vec<T: Clone>(input: &[T], chunk_size: usize) -> Vec<Vec<T>> {
        input.chunks(chunk_size).map(|c| c.to_vec()).collect()
}

/// Flatten a nested vector.
pub fn flatten<T: Clone>(input: &[Vec<T>]) -> Vec<T> {
    input.iter().flatten().cloned().collect()
}

/// Deduplicate a vector while preserving order.
pub fn dedup_preserve_order<T: Eq + Hash + Clone>(input: &[T]) -> Vec<T> {
    use std::collections::HashSet;
    let mut seen = HashSet::new();
    input
        .iter()
        .filter(|x| seen.insert(x.clone()))
        .cloned()
        .collect()
}

/// Interleave two vectors (merge by alternating elements).
pub fn interleave<T: Clone>(a: &[T], b: &[T]) -> Vec<T> {
    let mut result = Vec::with_capacity(a.len() + b.len());
    let max_len = a.len().max(b.len());
    for i in 0..max_len {
        if i < a.len() {
            result.push(a[i].clone());
        }
        if i < b.len() {
            result.push(b[i].clone());
        }
    }
    result
}

/// Split a vector into n roughly equal parts.
pub fn split_n<T: Clone>(input: &[T], n: usize) -> Vec<Vec<T>> {
    if n == 0 {
        return vec![input.to_vec()];
    }
    let chunk_size = (input.len() + n - 1) / n;
    input.chunks(chunk_size).map(|c| c.to_vec()).collect()
}

/// Find the top-k elements by score (descending).
pub fn top_k<T: Clone>(items: &[(T, f32)], k: usize) -> Vec<(T, f32)> {
    let mut items: Vec<(T, f32)> = items.to_vec();
    items.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));
    items.into_iter().take(k).collect()
}

/// Find the top-k indices by score (descending).
pub fn top_k_indices(scores: &[f32], k: usize) -> Vec<usize> {
    let mut indices: Vec<usize> = (0..scores.len()).collect();
    indices.sort_by(|&a, &b| {
        scores[b]
            .partial_cmp(&scores[a])
            .unwrap_or(std::cmp::Ordering::Equal)
    });
    indices.into_iter().take(k).collect()
}

/// Compute softmax over a slice.
pub fn softmax(scores: &[f32]) -> Vec<f32> {
    let max_score = scores
        .iter()
        .cloned()
        .fold(f32::NEG_INFINITY, f32::max);
    let exps: Vec<f32> = scores.iter().map(|x| (x - max_score).exp()).collect();
    let sum: f32 = exps.iter().sum();
    exps.iter().map(|x| x / sum).collect()
}

/// Compute mean of a slice.
pub fn mean(values: &[f32]) -> f32 {
    if values.is_empty() {
        return 0.0;
    }
    values.iter().sum::<f32>() / values.len() as f32
}

/// Compute standard deviation of a slice.
pub fn std_dev(values: &[f32]) -> f32 {
    if values.len() < 2 {
        return 0.0;
    }
    let m = mean(values);
    let variance: f32 = values.iter().map(|x| (x - m).powi(2)).sum::<f32>() / values.len() as f32;
    variance.sqrt()
}

/// Min-max normalization.
pub fn min_max_normalize(values: &[f32]) -> Vec<f32> {
    if values.is_empty() {
        return Vec::new();
    }
    let min = values.iter().cloned().fold(f32::INFINITY, f32::min);
    let max = values.iter().cloned().fold(f32::NEG_INFINITY, f32::max);
    let range = max - min;
    if range == 0.0 {
        return vec![0.5; values.len()];
    }
    values.iter().map(|x| (x - min) / range).collect()
}

/// Z-score normalization.
pub fn z_score_normalize(values: &[f32]) -> Vec<f32> {
    let m = mean(values);
    let sd = std_dev(values);
    if sd == 0.0 {
        return vec![0.0; values.len()];
    }
    values.iter().map(|x| (x - m) / sd).collect()
}

/// Compress bytes using zstd.
pub fn compress_zstd(data: &[u8]) -> crate::AerynResult<Vec<u8>> {
    zstd::encode_all(data, 3).map_err(|e| crate::aeryn_err!(Serialization, "Zstd compression failed: {}", e))
}

/// Decompress bytes using zstd.
pub fn decompress_zstd(data: &[u8]) -> crate::AerynResult<Vec<u8>> {
    zstd::decode_all(data).map_err(|e| crate::aeryn_err!(Deserialization, "Zstd decompression failed: {}", e))
}

/// Encode bytes to base64.
pub fn encode_base64(data: &[u8]) -> String {
    use base64::{engine::general_purpose, Engine as _};
    general_purpose::STANDARD.encode(data)
}

/// Decode base64 to bytes.
pub fn decode_base64(data: &str) -> crate::AerynResult<Vec<u8>> {
    use base64::{engine::general_purpose, Engine as _};
    general_purpose::STANDARD.decode(data).map_err(|e| crate::aeryn_err!(Deserialization, "Base64 decode failed: {}", e))
}

/// Generate a UUID v4 string.
pub fn generate_uuid() -> String {
    uuid::Uuid::new_v4().to_string()
}

/// Get current timestamp as ISO 8601 string.
pub fn now_iso() -> String {
    chrono::Utc::now().to_rfc3339()
}

/// Parse ISO 8601 timestamp.
pub fn parse_iso(s: &str) -> crate::AerynResult<chrono::DateTime<chrono::Utc>> {
    s.parse::<chrono::DateTime<chrono::Utc>>()
        .map_err(|e| crate::aeryn_err!(Validation, "Invalid ISO timestamp: {}", e))
}

/// Format bytes as human-readable string.
pub fn format_bytes(bytes: u64) -> String {
    const UNITS: &[&str] = &["B", "KB", "MB", "GB", "TB"];
    let mut size = bytes as f64;
    let mut unit_idx = 0;
    while size >= 1024.0 && unit_idx < UNITS.len() - 1 {
        size /= 1024.0;
        unit_idx += 1;
    }
    format!("{:.2} {}", size, UNITS[unit_idx])
}

/// Truncate a string to a maximum length with ellipsis.
pub fn truncate(s: &str, max_len: usize) -> String {
    if s.len() <= max_len {
        s.to_string()
    } else {
        format!("{}...", &s[..max_len.saturating_sub(3)])
    }
}

/// Count words in a string (Unicode-aware).
pub fn word_count(text: &str) -> usize {
    text.unicode_words().count()
}

/// Count sentences in a string.
pub fn sentence_count(text: &str) -> usize {
    text.split(|c| c == '.' || c == '!' || c == '?')
        .filter(|s| !s.trim().is_empty())
        .count()
}

/// Extract sentences from a string.
pub fn extract_sentences(text: &str) -> Vec<&str> {
    text.split(|c| c == '.' || c == '!' || c == '?')
        .filter(|s| !s.trim().is_empty())
        .map(|s| s.trim())
        .collect()
}

/// Check if a string is mostly ASCII.
pub fn is_mostly_ascii(text: &str) -> bool {
    let ascii_count = text.chars().filter(|c| c.is_ascii()).count();
    ascii_count * 100 / text.len().max(1) > 90
}

/// Detect language of a text (simple heuristic).
pub fn detect_language(text: &str) -> &'static str {
    if text.is_empty() {
        return "unknown";
    }
    // Simple heuristic based on character ranges
    let cjk_count = text.chars().filter(|c| ('\u{4e00}'..='\u{9fff}').contains(c)).count();
    let arabic_count = text.chars().filter(|c| ('\u{0600}'..='\u{06ff}').contains(c)).count();
    let cyrillic_count = text.chars().filter(|c| ('\u{0400}'..='\u{04ff}').contains(c)).count();
    let total = text.chars().count();

    if cjk_count * 100 / total > 30 {
        "zh"
    } else if arabic_count * 100 / total > 30 {
        "ar"
    } else if cyrillic_count * 100 / total > 30 {
        "ru"
    } else {
        "en"
    }
}

/// Retry a function with exponential backoff (synchronous).
pub fn retry_with_backoff<F, T>(
    mut f: F,
    max_retries: u32,
    base_delay_ms: u64,
) -> crate::AerynResult<T>
where
    F: FnMut() -> crate::AerynResult<T>,
{
    let mut last_error = None;
    for attempt in 0..=max_retries {
        match f() {
            Ok(result) => return Ok(result),
            Err(e) => {
                last_error = Some(e);
                if attempt < max_retries {
                    let delay = base_delay_ms * 2u64.pow(attempt);
                    std::thread::sleep(std::time::Duration::from_millis(delay));
                }
            }
        }
    }
    Err(last_error.unwrap_or_else(|| crate::aeryn_err!(Internal, "Retry failed")))
}

/// Measure execution time of a function.
pub fn measure_time<F, T>(f: F) -> (T, std::time::Duration)
where
    F: FnOnce() -> T,
{
    let start = std::time::Instant::now();
    let result = f();
    let elapsed = start.elapsed();
    (result, elapsed)
}

/// Convert a vector of f32 to bytes (little-endian).
pub fn f32_vec_to_bytes(vec: &[f32]) -> Vec<u8> {
    vec.iter()
        .flat_map(|x| x.to_le_bytes())
        .collect()
}

/// Convert bytes to a vector of f32 (little-endian).
pub fn bytes_to_f32_vec(bytes: &[u8]) -> Vec<f32> {
    bytes
        .chunks_exact(4)
        .map(|chunk| f32::from_le_bytes([chunk[0], chunk[1], chunk[2], chunk[3]]))
        .collect()
}

/// Compute the mean of multiple vectors.
pub fn mean_embedding(embeddings: &[Vec<f32>]) -> Vec<f32> {
    if embeddings.is_empty() {
        return Vec::new();
    }
    let dim = embeddings[0].len();
    let mut result = vec![0.0f32; dim];
    for emb in embeddings {
        for (i, &val) in emb.iter().enumerate() {
            if i < dim {
                result[i] += val;
            }
        }
    }
    let n = embeddings.len() as f32;
    for val in &mut result {
        *val /= n;
    }
    result
}

/// Weighted average of vectors.
pub fn weighted_mean_embedding(embeddings: &[Vec<f32>], weights: &[f32]) -> Vec<f32> {
    if embeddings.is_empty() || weights.is_empty() {
        return Vec::new();
    }
    let dim = embeddings[0].len();
    let mut result = vec![0.0f32; dim];
    let weight_sum: f32 = weights.iter().sum();
    if weight_sum == 0.0 {
        return result;
    }
    for (emb, &weight) in embeddings.iter().zip(weights.iter()) {
        for (i, &val) in emb.iter().enumerate() {
            if i < dim {
                result[i] += val * weight / weight_sum;
            }
        }
    }
    result
}

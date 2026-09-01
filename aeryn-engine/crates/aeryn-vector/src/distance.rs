//! Distance metrics for vector similarity.

use std::simd::*;

/// Available distance metrics.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum DistanceMetric {
    Cosine,
    DotProduct,
    Euclidean,
    Manhattan,
    Hamming,
}

impl DistanceMetric {
    pub fn from_str(s: &str) -> Option<Self> {
        match s.to_lowercase().as_str() {
            "cosine" => Some(DistanceMetric::Cosine),
            "dot" | "dot_product" | "inner" => Some(DistanceMetric::DotProduct),
            "euclidean" | "l2" => Some(DistanceMetric::Euclidean),
            "manhattan" | "l1" => Some(DistanceMetric::Manhattan),
            "hamming" => Some(DistanceMetric::Hamming),
            _ => None,
        }
    }

    pub fn is_similarity(&self) -> bool {
        matches!(self, DistanceMetric::Cosine | DistanceMetric::DotProduct)
    }

    pub fn is_distance(&self) -> bool {
        !self.is_similarity()
    }

    pub fn worst_value(&self) -> f32 {
        if self.is_similarity() {
            f32::NEG_INFINITY
        } else {
            f32::INFINITY
        }
    }

    pub fn best_value(&self) -> f32 {
        if self.is_similarity() {
            1.0
        } else {
            0.0
        }
    }
}

/// Compute distance between two vectors using the specified metric.
#[inline]
pub fn compute_distance(metric: DistanceMetric, a: &[f32], b: &[f32]) -> f32 {
    debug_assert_eq!(a.len(), b.len(), "Vector dimensions must match");
    match metric {
        DistanceMetric::Cosine => cosine_distance(a, b),
        DistanceMetric::DotProduct => dot_product_distance(a, b),
        DistanceMetric::Euclidean => euclidean_distance(a, b),
        DistanceMetric::Manhattan => manhattan_distance(a, b),
        DistanceMetric::Hamming => hamming_distance(a, b),
    }
}

/// Compute cosine distance (1 - cosine_similarity).
#[inline]
pub fn cosine_distance(a: &[f32], b: &[f32]) -> f32 {
    let dot_product: f32 = a.iter().zip(b.iter()).map(|(x, y)| x * y).sum();
    let norm_a: f32 = a.iter().map(|x| x * x).sum::<f32>().sqrt();
    let norm_b: f32 = b.iter().map(|x| x * x).sum::<f32>().sqrt();

    if norm_a == 0.0 || norm_b == 0.0 {
        1.0
    } else {
        1.0 - (dot_product / (norm_a * norm_b))
    }
}

/// Compute dot product (negated for use as distance).
#[inline]
pub fn dot_product_distance(a: &[f32], b: &[f32]) -> f32 {
    let dot_product: f32 = a.iter().zip(b.iter()).map(|(x, y)| x * y).sum();
    -dot_product
}

/// Compute Euclidean distance (L2 norm).
#[inline]
pub fn euclidean_distance(a: &[f32], b: &[f32]) -> f32 {
    a.iter()
        .zip(b.iter())
        .map(|(x, y)| (x - y).powi(2))
        .sum::<f32>()
        .sqrt()
}

/// Compute Manhattan distance (L1 norm).
#[inline]
pub fn manhattan_distance(a: &[f32], b: &[f32]) -> f32 {
    a.iter().zip(b.iter()).map(|(x, y)| (x - y).abs()).sum()
}

/// Compute Hamming distance (number of differing elements).
#[inline]
pub fn hamming_distance(a: &[f32], b: &[f32]) -> f32 {
    a.iter()
        .zip(b.iter())
        .filter(|(x, y)| (x - y).abs() > f32::EPSILON)
        .count() as f32
}

/// Compute squared Euclidean distance (skip sqrt for comparison-only use).
#[inline]
pub fn euclidean_distance_sq(a: &[f32], b: &[f32]) -> f32 {
    a.iter()
        .zip(b.iter())
        .map(|(x, y)| (x - y).powi(2))
        .sum()
}

/// Compute cosine similarity (not distance).
#[inline]
pub fn cosine_similarity(a: &[f32], b: &[f32]) -> f32 {
    let dot_product: f32 = a.iter().zip(b.iter()).map(|(x, y)| x * y).sum();
    let norm_a: f32 = a.iter().map(|x| x * x).sum::<f32>().sqrt();
    let norm_b: f32 = b.iter().map(|x| x * x).sum::<f32>().sqrt();

    if norm_a == 0.0 || norm_b == 0.0 {
        0.0
    } else {
        dot_product / (norm_a * norm_b)
    }
}

/// Compute dot product (not negated).
#[inline]
pub fn dot_product(a: &[f32], b: &[f32]) -> f32 {
    a.iter().zip(b.iter()).map(|(x, y)| x * y).sum()
}

/// Batch compute distances from a query to multiple vectors.
pub fn batch_compute_distances(metric: DistanceMetric, query: &[f32], vectors: &[Vec<f32>]) -> Vec<f32> {
    vectors.iter().map(|v| compute_distance(metric, query, v)).collect()
}

/// Parallel batch compute distances using Rayon.
pub fn par_batch_compute_distances(metric: DistanceMetric, query: &[f32], vectors: &[Vec<f32>]) -> Vec<f32> {
    use rayon::prelude::*;
    vectors.par_iter().map(|v| compute_distance(metric, query, v)).collect()
}

/// Find the index of the minimum distance.
pub fn argmin(distances: &[f32]) -> Option<usize> {
    distances.iter().enumerate().min_by(|(_, a), (_, b)| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal)).map(|(i, _)| i)
}

/// Find the index of the maximum similarity.
pub fn argmax(similarities: &[f32]) -> Option<usize> {
    similarities.iter().enumerate().max_by(|(_, a), (_, b)| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal)).map(|(i, _)| i)
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

/// Normalize a batch of vectors in parallel.
pub fn par_normalize_l2(vectors: &mut [Vec<f32>]) {
    use rayon::prelude::*;
    vectors.par_iter_mut().for_each(|v| normalize_l2(v));
}

/// Compute the centroid of a set of vectors.
pub fn compute_centroid(vectors: &[Vec<f32>]) -> Option<Vec<f32>> {
    if vectors.is_empty() {
        return None;
    }
    let dim = vectors[0].len();
    let mut centroid = vec![0.0f32; dim];
    for v in vectors {
        for (i, &val) in v.iter().enumerate() {
            if i < dim {
                centroid[i] += val;
            }
        }
    }
    let n = vectors.len() as f32;
    for val in &mut centroid {
        *val /= n;
    }
    Some(centroid)
}

/// Compute pairwise distances between all vectors.
pub fn pairwise_distances(metric: DistanceMetric, vectors: &[Vec<f32>]) -> Vec<Vec<f32>> {
    let n = vectors.len();
    let mut distances = vec![vec![0.0f32; n]; n];
    for i in 0..n {
        for j in (i + 1)..n {
            let d = compute_distance(metric, &vectors[i], &vectors[j]);
            distances[i][j] = d;
            distances[j][i] = d;
        }
    }
    distances
}

/// Parallel pairwise distances.
pub fn par_pairwise_distances(metric: DistanceMetric, vectors: &[Vec<f32>]) -> Vec<Vec<f32>> {
    use rayon::prelude::*;
    let n = vectors.len();
    let mut distances = vec![vec![0.0f32; n]; n];
    
    let results: Vec<(usize, usize, f32)> = (0..n)
        .into_par_iter()
        .flat_map(|i| {
            ((i + 1)..n)
                .into_par_iter()
                .map(move |j| {
                    let d = compute_distance(metric, &vectors[i], &vectors[j]);
                    (i, j, d)
                })
                .collect::<Vec<_>>()
        })
        .collect();
    
    for (i, j, d) in results {
        distances[i][j] = d;
        distances[j][i] = d;
    }
    
    distances
}

/// Distance cache for repeated queries.
pub struct DistanceCache {
    metric: DistanceMetric,
    cache: hashbrown::HashMap<(u64, u64), f32>,
}

impl DistanceCache {
    pub fn new(metric: DistanceMetric) -> Self {
        Self {
            metric,
            cache: hashbrown::HashMap::new(),
        }
    }

    pub fn compute_or_cache<F: FnOnce() -> f32>(&mut self, hash_a: u64, hash_b: u64, compute: F) -> f32 {
        let key = if hash_a < hash_b { (hash_a, hash_b) } else { (hash_b, hash_a) };
        *self.cache.entry(key).or_insert_with(compute)
    }

    pub fn len(&self) -> usize {
        self.cache.len()
    }

    pub fn is_empty(&self) -> bool {
        self.cache.is_empty()
    }

    pub fn clear(&mut self) {
        self.cache.clear()
    }
}

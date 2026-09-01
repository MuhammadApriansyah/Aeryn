//! Distance metrics for vector similarity.

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum DistanceMetric {
    Cosine,
    DotProduct,
    Euclidean,
    Manhattan,
}

impl DistanceMetric {
    pub fn from_str(s: &str) -> Option<Self> {
        match s {
            "cosine" => Some(DistanceMetric::Cosine),
            "dot" | "dot_product" => Some(DistanceMetric::DotProduct),
            "euclidean" | "l2" => Some(DistanceMetric::Euclidean),
            "manhattan" | "l1" => Some(DistanceMetric::Manhattan),
            _ => None,
        }
    }
}

#[inline]
pub fn compute_distance(metric: DistanceMetric, a: &[f32], b: &[f32]) -> f32 {
    match metric {
        DistanceMetric::Cosine => cosine_distance(a, b),
        DistanceMetric::DotProduct => -dot_product(a, b),
        DistanceMetric::Euclidean => euclidean_distance(a, b),
        DistanceMetric::Manhattan => manhattan_distance(a, b),
    }
}

#[inline]
pub fn cosine_distance(a: &[f32], b: &[f32]) -> f32 {
    let dot = dot_product(a, b);
    let norm_a = a.iter().map(|x| x * x).sum::<f32>().sqrt();
    let norm_b = b.iter().map(|x| x * x).sum::<f32>().sqrt();
    
    if norm_a == 0.0 || norm_b == 0.0 {
        1.0
    } else {
        1.0 - (dot / (norm_a * norm_b))
    }
}

#[inline]
pub fn cosine_similarity(a: &[f32], b: &[f32]) -> f32 {
    let dot = dot_product(a, b);
    let norm_a = a.iter().map(|x| x * x).sum::<f32>().sqrt();
    let norm_b = b.iter().map(|x| x * x).sum::<f32>().sqrt();
    
    if norm_a == 0.0 || norm_b == 0.0 {
        0.0
    } else {
        dot / (norm_a * norm_b)
    }
}

#[inline]
pub fn dot_product(a: &[f32], b: &[f32]) -> f32 {
    a.iter().zip(b.iter()).map(|(x, y)| x * y).sum()
}

#[inline]
pub fn euclidean_distance(a: &[f32], b: &[f32]) -> f32 {
    a.iter().zip(b.iter()).map(|(x, y)| (x - y).powi(2)).sum::<f32>().sqrt()
}

#[inline]
pub fn manhattan_distance(a: &[f32], b: &[f32]) -> f32 {
    a.iter().zip(b.iter()).map(|(x, y)| (x - y).abs()).sum()
}

pub fn normalize_l2(vector: &mut [f32]) {
    let norm = vector.iter().map(|x| x * x).sum::<f32>().sqrt();
    if norm > 0.0 {
        for x in vector.iter_mut() {
            *x /= norm;
        }
    }
}

pub fn compute_centroid(vectors: &[Vec<f32>]) -> Option<Vec<f32>> {
    if vectors.is_empty() {
        return None;
    }
    let dim = vectors[0].len();
    let mut centroid = vec![0.0f32; dim];
    for v in vectors {
        for (i, &val) in v.iter().enumerate().take(dim) {
            centroid[i] += val;
        }
    }
    let n = vectors.len() as f32;
    for val in &mut centroid {
        *val /= n;
    }
    Some(centroid)
}

pub fn top_k(scores: &[(usize, f32)], k: usize) -> Vec<(usize, f32)> {
    let mut sorted = scores.to_vec();
    sorted.sort_by(|a, b| a.1.partial_cmp(&b.1).unwrap_or(std::cmp::Ordering::Equal));
    sorted.truncate(k);
    sorted
}

pub fn top_k_similarity(scores: &[(usize, f32)], k: usize) -> Vec<(usize, f32)> {
    let mut sorted = scores.to_vec();
    sorted.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));
    sorted.truncate(k);
    sorted
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_cosine_similarity_identical() {
        let v = vec![1.0, 2.0, 3.0];
        assert!((cosine_similarity(&v, &v) - 1.0).abs() < 1e-6);
    }

    #[test]
    fn test_cosine_similarity_orthogonal() {
        let a = vec![1.0, 0.0];
        let b = vec![0.0, 1.0];
        assert!(cosine_similarity(&a, &b).abs() < 1e-6);
    }

    #[test]
    fn test_euclidean_distance() {
        let a = vec![0.0, 0.0];
        let b = vec![3.0, 4.0];
        assert!((euclidean_distance(&a, &b) - 5.0).abs() < 1e-6);
    }

    #[test]
    fn test_manhattan_distance() {
        let a = vec![0.0, 0.0];
        let b = vec![3.0, 4.0];
        assert!((manhattan_distance(&a, &b) - 7.0).abs() < 1e-6);
    }

    #[test]
    fn test_normalize_l2() {
        let mut v = vec![3.0, 4.0];
        normalize_l2(&mut v);
        assert!((v[0] - 0.6).abs() < 1e-6);
        assert!((v[1] - 0.8).abs() < 1e-6);
    }

    #[test]
    fn test_top_k() {
        let scores = vec![(0, 0.5), (1, 0.9), (2, 0.1), (3, 0.7)];
        let result = top_k(&scores, 2);
        assert_eq!(result.len(), 2);
        assert_eq!(result[0].0, 2);
        assert_eq!(result[1].0, 0);
    }
}

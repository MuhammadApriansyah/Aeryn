use std::ffi::{CStr, CString};
use std::os::raw::c_char;
use std::collections::HashMap;

// ========================================
// DISTANCE METRICS
// ========================================

#[no_mangle]
pub extern "C" fn cosine_similarity(a: *const f32, b: *const f32, len: usize) -> f32 {
    if a.is_null() || b.is_null() || len == 0 {
        return 0.0;
    }
    let a = unsafe { std::slice::from_raw_parts(a, len) };
    let b = unsafe { std::slice::from_raw_parts(b, len) };
    let dot: f32 = a.iter().zip(b.iter()).map(|(x, y)| x * y).sum();
    let norm_a: f32 = a.iter().map(|x| x * x).sum::<f32>().sqrt();
    let norm_b: f32 = b.iter().map(|x| x * x).sum::<f32>().sqrt();
    if norm_a == 0.0 || norm_b == 0.0 {
        0.0
    } else {
        dot / (norm_a * norm_b)
    }
}

#[no_mangle]
pub extern "C" fn euclidean_distance(a: *const f32, b: *const f32, len: usize) -> f32 {
    if a.is_null() || b.is_null() || len == 0 {
        return f32::MAX;
    }
    let a = unsafe { std::slice::from_raw_parts(a, len) };
    let b = unsafe { std::slice::from_raw_parts(b, len) };
    a.iter().zip(b.iter()).map(|(x, y)| (x - y).powi(2)).sum::<f32>().sqrt()
}

// ========================================
// HASHING
// ========================================

fn bytes_to_hex(bytes: &[u8]) -> String {
    let mut result = String::new();
    for b in bytes {
        let high = b >> 4;
        let low = b & 0xf;
        result.push(if high < 10 { b'0' + high } else { b'a' + high - 10 } as char);
        result.push(if low < 10 { b'0' + low } else { b'a' + low - 10 } as char);
    }
    result
}

#[no_mangle]
pub extern "C" fn hash_text(input: *const c_char) -> *mut c_char {
    if input.is_null() {
        return std::ptr::null_mut();
    }
    let input = unsafe { CStr::from_ptr(input) }.to_str().unwrap_or("");
    let hash = {
        use sha2::{Digest, Sha256};
        let mut hasher = Sha256::new();
        hasher.update(input.as_bytes());
        let result = hasher.finalize();
        bytes_to_hex(&result)
    };
    CString::new(hash).unwrap().into_raw()
}

#[no_mangle]
pub extern "C" fn free_string(s: *mut c_char) {
    if !s.is_null() {
        unsafe { drop(CString::from_raw(s)) };
    }
}

// ========================================
// TEXT PROCESSING
// ========================================

#[no_mangle]
pub extern "C" fn word_count(text: *const c_char) -> usize {
    if text.is_null() {
        return 0;
    }
    let text = unsafe { CStr::from_ptr(text) }.to_str().unwrap_or("");
    text.split_whitespace().count()
}

#[no_mangle]
pub extern "C" fn truncate_text(text: *const c_char, max_len: usize) -> *mut c_char {
    if text.is_null() {
        return std::ptr::null_mut();
    }
    let text = unsafe { CStr::from_ptr(text) }.to_str().unwrap_or("");
    let result = if text.len() <= max_len {
        text.to_string()
    } else {
        format!("{}...", &text[..max_len.saturating_sub(3)])
    };
    CString::new(result).unwrap().into_raw()
}

// ========================================
// VECTOR SEARCH HELPERS
// ========================================

#[no_mangle]
pub extern "C" fn find_top_k(
    query: *const f32,
    query_len: usize,
    vectors: *const f32,
    num_vectors: usize,
    dim: usize,
    k: usize,
    out_indices: *mut usize,
    out_scores: *mut f32,
) -> usize {
    if query.is_null() || vectors.is_null() || out_indices.is_null() || out_scores.is_null() {
        return 0;
    }
    
    let all_vectors = unsafe { std::slice::from_raw_parts(vectors, num_vectors * dim) };
    
    let mut results: Vec<(usize, f32)> = Vec::new();
    
    for i in 0..num_vectors {
        let start = i * dim;
        let vec_ptr = unsafe { all_vectors.as_ptr().add(start) };
        let score = cosine_similarity(query, vec_ptr, dim);
        results.push((i, score));
    }
    
    results.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));
    
    let k = k.min(results.len());
    for i in 0..k {
        unsafe {
            *out_indices.add(i) = results[i].0;
            *out_scores.add(i) = results[i].1;
        }
    }
    
    k
}

// ========================================
// TESTS
// ========================================

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_cosine_similarity() {
        let a = vec![1.0f32, 2.0, 3.0];
        let b = vec![1.0f32, 2.0, 3.0];
        let sim = cosine_similarity(a.as_ptr(), b.as_ptr(), 3);
        assert!((sim - 1.0).abs() < 1e-5);
    }

    #[test]
    fn test_cosine_orthogonal() {
        let a = vec![1.0f32, 0.0];
        let b = vec![0.0f32, 1.0];
        let sim = cosine_similarity(a.as_ptr(), b.as_ptr(), 2);
        assert!(sim.abs() < 1e-5);
    }

    #[test]
    fn test_euclidean_distance() {
        let a = vec![0.0f32, 0.0];
        let b = vec![3.0f32, 4.0];
        let dist = euclidean_distance(a.as_ptr(), b.as_ptr(), 2);
        assert!((dist - 5.0).abs() < 1e-5);
    }

    #[test]
    fn test_hash_text() {
        let input = CString::new("hello").unwrap();
        let hash = hash_text(input.as_ptr());
        assert!(!hash.is_null());
        unsafe {
            let hash_str = CStr::from_ptr(hash).to_str().unwrap();
            assert_eq!(hash_str.len(), 64);
            free_string(hash);
        }
    }

    #[test]
    fn test_word_count() {
        let text = CString::new("Hello world this is a test").unwrap();
        let count = word_count(text.as_ptr());
        assert_eq!(count, 6);
    }

    #[test]
    fn test_find_top_k() {
        let query = vec![1.0f32, 0.0, 0.0];
        let vectors = vec![
            1.0, 0.0, 0.0,  // index 0: identical
            0.0, 1.0, 0.0,  // index 1: orthogonal
            0.5, 0.5, 0.0,  // index 2: partial
        ];
        let mut out_indices = vec![0usize; 3];
        let mut out_scores = vec![0.0f32; 3];
        
        let k = find_top_k(
            query.as_ptr(), 3,
            vectors.as_ptr(), 3, 3,
            3,
            out_indices.as_mut_ptr(),
            out_scores.as_mut_ptr(),
        );
        
        assert_eq!(k, 3);
        assert_eq!(out_indices[0], 0);  // identical first
        assert!(out_scores[0] > out_scores[1]);
    }
}

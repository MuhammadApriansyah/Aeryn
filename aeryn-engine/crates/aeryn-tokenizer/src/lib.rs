use std::collections::HashMap;

use parking_lot::RwLock;
use regex::Regex;
use serde::{Deserialize, Serialize};
use unicode_segmentation::UnicodeSegmentation;

/// Configuration for the tokenizer.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TokenizerConfig {
    pub cache_size: usize,
    pub unicode_words: bool,
    pub lowercase: bool,
    pub min_token_length: usize,
    pub max_token_length: usize,
    pub strip_punctuation: bool,
    pub stopwords: Vec<String>,
}

impl Default for TokenizerConfig {
    fn default() -> Self {
        Self {
            cache_size: 10_000,
            unicode_words: true,
            lowercase: false,
            min_token_length: 1,
            max_token_length: 100,
            strip_punctuation: false,
            stopwords: Vec::new(),
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct Token {
    pub text: String,
    pub start: usize,
    pub end: usize,
}

impl Token {
    pub fn new(text: &str, start: usize, end: usize) -> Self {
        Self {
            text: text.to_string(),
            start,
            end,
        }
    }
}

pub struct Tokenizer {
    config: TokenizerConfig,
    cache: RwLock<lru::LruCache<String, Vec<String>>>,
    word_pattern: Regex,
    stopwords_set: std::collections::HashSet<String>,
}

impl Tokenizer {
    pub fn new(config: TokenizerConfig) -> Self {
        let cache_size = std::num::NonZeroUsize::new(config.cache_size).unwrap();
        let word_pattern = Regex::new(r"\b\w+\b").unwrap();
        let stopwords_set: std::collections::HashSet<String> =
            config.stopwords.iter().cloned().collect();

        Self {
            config,
            cache: RwLock::new(lru::LruCache::new(cache_size)),
            word_pattern,
            stopwords_set,
        }
    }

    pub fn with_default_config() -> Self {
        Self::new(TokenizerConfig::default())
    }

    pub fn count_tokens(&self, text: &str) -> usize {
        self.tokenize(text).len()
    }

    pub fn tokenize(&self, text: &str) -> Vec<String> {
        {
            let mut cache = self.cache.write();
            if let Some(cached) = cache.get(text) {
                return cached.clone();
            }
        }

        let tokens: Vec<String> = if self.config.unicode_words {
            text.unicode_words()
                .map(|w| w.to_string())
                .filter(|w| self.is_valid_token(w))
                .collect()
        } else {
            text.split_whitespace()
                .map(|w| w.to_string())
                .filter(|w| self.is_valid_token(w))
                .collect()
        };

        {
            let mut cache = self.cache.write();
            cache.put(text.to_string(), tokens.clone());
        }

        tokens
    }

    fn is_valid_token(&self, token: &str) -> bool {
        let token = if self.config.lowercase {
            token.to_lowercase()
        } else {
            token.to_string()
        };

        let len = token.len();
        if len < self.config.min_token_length || len > self.config.max_token_length {
            return false;
        }

        if self.stopwords_set.contains(&token) {
            return false;
        }

        true
    }
}

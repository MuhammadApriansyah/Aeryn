//! Tokenizer with LRU cache and multiple backends.

use std::collections::HashMap;
use std::sync::Arc;

use hashbrown::HashMap as FastHashMap;
use lru::LruCache;
use parking_lot::RwLock;
use regex::Regex;
use serde::{Deserialize, Serialize};
use unicode_segmentation::UnicodeSegmentation;

/// Configuration for the tokenizer.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TokenizerConfig {
    /// Maximum cache size.
    pub cache_size: usize,
    /// Whether to use Unicode word boundaries.
    pub unicode_words: bool,
    /// Whether to lowercase tokens.
    pub lowercase: bool,
    /// Minimum token length.
    pub min_token_length: usize,
    /// Maximum token length.
    pub max_token_length: usize,
    /// Whether to strip punctuation.
    pub strip_punctuation: bool,
    /// Custom stopwords.
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

/// A token with metadata.
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct Token {
    pub text: String,
    pub start: usize,
    pub end: usize,
}

impl Token {
    pub fn new(text: impl Into<String>, start: usize, end: usize) -> Self {
        Self {
            text: text.into(),
            start,
            end,
        }
    }
}

/// Tokenizer with caching support.
pub struct Tokenizer {
    config: TokenizerConfig,
    cache: RwLock<LruCache<String, Vec<String>>>,
    word_pattern: Regex,
    stopwords_set: hashbrown::HashSet<String>,
}

impl Tokenizer {
    pub fn new(config: TokenizerConfig) -> Self {
        let cache_size = config.cache_size;
        let word_pattern = Regex::new(r"\b\w+\b").unwrap();
        let stopwords_set: hashbrown::HashSet<String> =
            config.stopwords.iter().cloned().collect();

        Self {
            config,
            cache: RwLock::new(LruCache::new(
                std::num::NonZeroUsize::new(cache_size).unwrap(),
            )),
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

        let tokens = if self.config.unicode_words {
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

    pub fn tokenize_with_positions(&self, text: &str) -> Vec<Token> {
        text.unicode_words()
            .filter(|w| self.is_valid_token(w))
            .map(|word| {
                let start = word.as_ptr() as usize - text.as_ptr() as usize;
                let end = start + word.len();
                Token::new(word.to_string(), start, end)
            })
            .collect()
    }

    pub fn detokenize(&self, tokens: &[String]) -> String {
        tokens.join(" ")
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

        if self.config.strip_punctuation && token.chars().all(|c| c.is_ascii_punctuation()) {
            return false;
        }

        if self.stopwords_set.contains(&token) {
            return false;
        }

        true
    }

    pub fn get_config(&self) -> &TokenizerConfig {
        &self.config
    }

    pub fn clear_cache(&self) {
        self.cache.write().clear();
    }

    pub fn cache_len(&self) -> usize {
        self.cache.read().len()
    }

    pub fn vocabulary(&self, texts: &[impl AsRef<str>]) -> Vec<String> {
        let mut vocab: hashbrown::HashSet<String> = hashbrown::HashSet::new();
        for text in texts {
            for token in self.tokenize(text.as_ref()) {
                vocab.insert(token);
            }
        }
        let mut result: Vec<String> = vocab.into_iter().collect();
        result.sort();
        result
    }
}

impl std::fmt::Debug for Tokenizer {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("Tokenizer")
            .field("config", &self.config)
            .field("cache_len", &self.cache_len())
            .finish()
    }
}

use std::cmp;

use serde::{Deserialize, Serialize};

/// Configuration for recursive character text splitter.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SplitterConfig {
    /// Maximum size of each chunk in characters.
    pub chunk_size: usize,
    /// Number of characters to overlap between chunks.
    pub chunk_overlap: usize,
    /// Separators to use, in order of preference.
    pub separators: Vec<String>,
    /// Whether to keep separators in chunks.
    pub keep_separator: bool,
    /// Whether to strip whitespace from chunks.
    pub strip_whitespace: bool,
    /// Minimum chunk size (smaller chunks are merged).
    pub min_chunk_size: usize,
    /// Function to compute length (character or token count).
    pub length_function: LengthFunction,
}

impl Default for SplitterConfig {
    fn default() -> Self {
        Self {
            chunk_size: 1000,
            chunk_overlap: 200,
            separators: vec![
                "\n\n".to_string(),
                "\n".to_string(),
                ". ".to_string(),
                ", ".to_string(),
                " ".to_string(),
                "".to_string(),
            ],
            keep_separator: true,
            strip_whitespace: true,
            min_chunk_size: 50,
            length_function: LengthFunction::Characters,
        }
    }
}

/// How to compute text length.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum LengthFunction {
    Characters,
    ApproximateTokens,
}

impl LengthFunction {
    pub fn compute(&self, text: &str) -> usize {
        match self {
            LengthFunction::Characters => text.chars().count(),
            LengthFunction::ApproximateTokens => {
                // Rough approximation: 1 token ≈ 4 characters
                text.chars().count() / 4
            }
        }
    }
}

/// Recursive character text splitter.
pub struct RecursiveCharacterTextSplitter {
    config: SplitterConfig,
}

impl RecursiveCharacterTextSplitter {
    pub fn new(config: SplitterConfig) -> Self {
        Self { config }
    }

    pub fn with_default_config() -> Self {
        Self::new(SplitterConfig::default())
    }

    pub fn split_text(&self, text: &str) -> Vec<String> {
        let text = if self.config.strip_whitespace {
            text.trim()
        } else {
            text
        };

        if text.is_empty() {
            return Vec::new();
        }

        let chunks = self.recursive_split(text, &self.config.separators);

        // Merge small chunks
        self.merge_chunks(chunks)
    }

    pub fn split_texts(&self, texts: &[impl AsRef<str>]) -> Vec<String> {
        texts.iter().flat_map(|t| self.split_text(t.as_ref())).collect()
    }

    fn recursive_split(&self, text: &str, separators: &[String]) -> Vec<String> {
        if text.is_empty() {
            return Vec::new();
        }

        let text_len = self.config.length_function.compute(text);
        if text_len <= self.config.chunk_size {
            return vec![text.to_string()];
        }

        if separators.is_empty() {
            return self.split_by_size(text);
        }

        let separator = &separators[0];
        let rest = &separators[1..];

        let splits = if separator.is_empty() {
            self.split_by_size(text)
        } else {
            self.split_by_separator(text, separator)
        };

        let mut chunks = Vec::new();
        let mut current_chunk = String::new();

        for split in splits {
            let candidate = if current_chunk.is_empty() {
                split.clone()
            } else if self.config.keep_separator {
                format!("{}{}{}", current_chunk, separator, split)
            } else {
                format!("{}{}", current_chunk, split)
            };

            let candidate_len = self.config.length_function.compute(&candidate);

            if candidate_len <= self.config.chunk_size {
                current_chunk = candidate;
            } else {
                if !current_chunk.is_empty() {
                    chunks.push(current_chunk.clone());
                    current_chunk = self.handle_overlap(&current_chunk, &split, separator);
                } else {
                    let sub_chunks = if rest.is_empty() {
                        self.split_by_size(&split)
                    } else {
                        self.recursive_split(&split, rest)
                    };
                    chunks.extend(sub_chunks);
                }
            }
        }

        if !current_chunk.is_empty() {
            chunks.push(current_chunk);
        }

        chunks
    }

    fn split_by_separator(&self, text: &str, separator: &str) -> Vec<String> {
        let mut result = Vec::new();
        let mut start = 0;
        while let Some(pos) = text[start..].find(separator) {
            let end = start + pos;
            result.push(text[start..end].to_string());
            start = end + separator.len();
        }
        if start < text.len() {
            result.push(text[start..].to_string());
        }
        result
    }

    fn split_by_size(&self, text: &str) -> Vec<String> {
        let mut chunks = Vec::new();
        let size = self.config.chunk_size;
        let len = text.chars().count();
        let mut start = 0;

        while start < len {
            let end = cmp::min(start + size, len);
            let chunk: String = text.chars().skip(start).take(end - start).collect();
            chunks.push(chunk);
            start = end;
        }

        chunks
    }

    fn handle_overlap(&self, prev: &str, current: &str, separator: &str) -> String {
        if self.config.chunk_overlap == 0 {
            return current.to_string();
        }

        let overlap_chars = self.config.chunk_overlap.min(self.config.length_function.compute(prev));
        if overlap_chars == 0 {
            return current.to_string();
        }

        let prev_overlap: String = prev.chars().rev().take(overlap_chars).collect::<String>().chars().rev().collect();
        
        if self.config.keep_separator {
            format!("{}{}{}", prev_overlap, separator, current)
        } else {
            format!("{}{}", prev_overlap, current)
        }
    }

    fn merge_chunks(&self, chunks: Vec<String>) -> Vec<String> {
        if chunks.is_empty() {
            return chunks;
        }

        let mut merged = Vec::new();
        let mut current = chunks[0].clone();

        for chunk in &chunks[1..] {
            let current_len = self.config.length_function.compute(&current);
            let chunk_len = self.config.length_function.compute(chunk);

            if current_len + chunk_len + 1 <= self.config.chunk_size
                || chunk_len < self.config.min_chunk_size
            {
                current.push(' ');
                current.push_str(chunk);
            } else {
                merged.push(current);
                current = chunk.clone();
            }
        }

        merged.push(current);
        merged
    }

    /// Create documents from a single text with metadata.
    pub fn create_documents(
        &self,
        text: &str,
        metadata: Option<std::collections::HashMap<String, String>>,
    ) -> Vec<Document> {
        self.split_text(text)
            .into_iter()
            .enumerate()
            .map(|(i, content)| {
                let mut doc_metadata = metadata.clone().unwrap_or_default();
                doc_metadata.insert("chunk_index".to_string(), i.to_string());
                Document {
                    content,
                    metadata: doc_metadata,
                }
            })
            .collect()
    }

    /// Create documents from multiple texts.
    pub fn create_documents_from_texts(
        &self,
        texts: &[impl AsRef<str>],
        metadatas: Option<&[std::collections::HashMap<String, String>]>,
    ) -> Vec<Document> {
        texts.iter().enumerate().flat_map(|(i, text)| {
            let metadata = metadatas.and_then(|m| m.get(i).cloned());
            self.create_documents(text.as_ref(), metadata)
        }).collect()
    }
}

/// A split document with metadata.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Document {
    pub content: String,
    pub metadata: std::collections::HashMap<String, String>,
}

impl Document {
    pub fn new(content: impl Into<String>) -> Self {
        Self {
            content: content.into(),
            metadata: std::collections::HashMap::new(),
        }
    }

    pub fn with_metadata(mut self, key: impl Into<String>, value: impl Into<String>) -> Self {
        self.metadata.insert(key.into(), value.into());
        self
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_split_by_size() {
        let splitter = RecursiveCharacterTextSplitter::new(SplitterConfig {
            chunk_size: 10,
            chunk_overlap: 0,
            separators: vec!["".to_string()],
            keep_separator: false,
            strip_whitespace: true,
            min_chunk_size: 0,
            length_function: LengthFunction::Characters,
        });

        let chunks = splitter.split_text("Hello world this is a test");
        assert_eq!(chunks.len(), 3);
        assert_eq!(chunks[0], "Hello worl");
    }

    #[test]
    fn test_merge_small_chunks() {
        let splitter = RecursiveCharacterTextSplitter::new(SplitterConfig {
            chunk_size: 100,
            chunk_overlap: 0,
            separators: vec![" ".to_string(), "".to_string()],
            keep_separator: false,
            strip_whitespace: true,
            min_chunk_size: 10,
            length_function: LengthFunction::Characters,
        });

        let chunks = splitter.split_text("a b c d e f g h i j k l m n o p");
        assert!(chunks.len() < 16);
    }
}

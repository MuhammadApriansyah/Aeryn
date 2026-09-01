use serde::{Deserialize, Serialize};

/// Configuration for token-based text splitter.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TokenizerConfig {
    /// Maximum tokens per chunk.
    pub chunk_size: usize,
    /// Token overlap between chunks.
    pub chunk_overlap: usize,
    /// Tokenizer model to use.
    pub model: TokenizerModel,
    /// Whether to keep separator tokens.
    pub keep_separator: bool,
    /// Whether to strip whitespace.
    pub strip_whitespace: bool,
}

impl Default for TokenizerConfig {
    fn default() -> Self {
        Self {
            chunk_size: 512,
            chunk_overlap: 50,
            model: TokenizerModel::Cl100kBase,
            keep_separator: true,
            strip_whitespace: true,
        }
    }
}

/// Supported tokenizer models.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum TokenizerModel {
    Cl100kBase,
    P50kBase,
    R50kBase,
    Gpt2,
    O200kBase,
}

impl TokenizerModel {
    pub fn from_str(s: &str) -> Option<Self> {
        match s.to_lowercase().as_str() {
            "cl100k_base" | "cl100k" => Some(TokenizerModel::Cl100kBase),
            "p50k_base" | "p50k" => Some(TokenizerModel::P50kBase),
            "r50k_base" | "r50k" => Some(TokenizerModel::R50kBase),
            "gpt2" => Some(TokenizerModel::Gpt2),
            "o200k_base" | "o200k" => Some(TokenizerModel::O200kBase),
            _ => None,
        }
    }
}

/// Token-based text splitter.
pub struct TokenTextSplitter {
    config: TokenizerConfig,
}

impl TokenTextSplitter {
    pub fn new(config: TokenizerConfig) -> Self {
        Self { config }
    }

    pub fn with_default_config() -> Self {
        Self::new(TokenizerConfig::default())
    }

    pub fn split_text(&self, text: &str) -> Vec<String> {
        if text.is_empty() {
            return Vec::new();
        }

        let text = if self.config.strip_whitespace {
            text.trim()
        } else {
            text
        };

        // Simple whitespace-based tokenization as fallback
        let tokens: Vec<&str> = text.split_whitespace().collect();
        let total_tokens = tokens.len();

        if total_tokens <= self.config.chunk_size {
            return vec![text.to_string()];
        }

        let mut chunks = Vec::new();
        let mut start = 0;

        while start < total_tokens {
            let end = (start + self.config.chunk_size).min(total_tokens);
            let chunk_tokens = &tokens[start..end];
            let chunk = chunk_tokens.join(" ");
            chunks.push(chunk);

            if end >= total_tokens {
                break;
            }

            // Advance with overlap
            start += self.config.chunk_size - self.config.chunk_overlap;
        }

        chunks
    }

    pub fn split_texts(&self, texts: &[impl AsRef<str>]) -> Vec<String> {
        texts.iter().flat_map(|t| self.split_text(t.as_ref())).collect()
    }

    pub fn count_tokens(&self, text: &str) -> usize {
        if text.is_empty() {
            return 0;
        }
        text.split_whitespace().count()
    }

    pub fn count_chunks(&self, text: &str) -> usize {
        self.split_text(text).len()
    }

    pub fn get_config(&self) -> &TokenizerConfig {
        &self.config
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_split_by_tokens() {
        let splitter = TokenTextSplitter::new(TokenizerConfig {
            chunk_size: 5,
            chunk_overlap: 0,
            model: TokenizerModel::Cl100kBase,
            keep_separator: false,
            strip_whitespace: true,
        });

        let text = "one two three four five six seven eight nine ten";
        let chunks = splitter.split_text(text);
        assert_eq!(chunks.len(), 2);
        assert_eq!(chunks[0], "one two three four five");
        assert_eq!(chunks[1], "six seven eight nine ten");
    }

    #[test]
    fn test_split_with_overlap() {
        let splitter = TokenTextSplitter::new(TokenizerConfig {
            chunk_size: 4,
            chunk_overlap: 1,
            model: TokenizerModel::Cl100kBase,
            keep_separator: false,
            strip_whitespace: true,
        });

        let text = "a b c d e f g h i j k l m n o p";
        let chunks = splitter.split_text(text);
        assert!(chunks.len() > 2);
    }
}

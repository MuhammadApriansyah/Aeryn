// Aeryn Engine — File Processor Module

use std::collections::HashMap;
use std::path::Path;
use std::fs;

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProcessedFile {
    pub path: String,
    pub file_type: String,
    pub content: String,
    pub chunks: Vec<String>,
    pub metadata: HashMap<String, String>,
}

pub struct FileProcessor {
    chunk_size: usize,
    chunk_overlap: usize,
}

impl FileProcessor {
    pub fn new(chunk_size: usize, chunk_overlap: usize) -> Self {
        Self { chunk_size, chunk_overlap }
    }

    pub fn default() -> Self {
        Self::new(1000, 200)
    }

    pub fn process_file(&self, path: &str) -> Result<ProcessedFile, String> {
        let path = Path::new(path);
        
        if !path.exists() {
            return Err(format!("File not found: {}", path.display()));
        }

        let content = fs::read_to_string(path).map_err(|e| e.to_string())?;
        let extension = path.extension()
            .and_then(|e| e.to_str())
            .unwrap_or("")
            .to_string();
        
        let chunks = self.split_text(&content);
        let mut metadata = HashMap::new();
        metadata.insert("file_name".to_string(), path.file_name().unwrap().to_string_lossy().to_string());
        metadata.insert("file_size".to_string(), content.len().to_string());

        Ok(ProcessedFile {
            path: path.to_string_lossy().to_string(),
            file_type: extension,
            content,
            chunks,
            metadata,
        })
    }

    pub fn process_text(&self, text: &str) -> Result<ProcessedFile, String> {
        let chunks = self.split_text(text);
        let mut metadata = HashMap::new();
        metadata.insert("content_length".to_string(), text.len().to_string());

        Ok(ProcessedFile {
            path: "memory".to_string(),
            file_type: "text".to_string(),
            content: text.to_string(),
            chunks,
            metadata,
        })
    }

    fn split_text(&self, text: &str) -> Vec<String> {
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

    pub fn extract_text(&self, content: &str, file_type: &str) -> String {
        match file_type.to_lowercase().as_str() {
            "html" | "htm" => {
                let re = regex::Regex::new(r"<[^>]+>").unwrap();
                re.replace_all(content, "").to_string()
            }
            "json" => {
                if let Ok(json) = serde_json::from_str::<serde_json::Value>(content) {
                    json.to_string()
                } else {
                    content.to_string()
                }
            }
            _ => content.to_string(),
        }
    }
}

#[cfg(test)]
mod processor_tests {
    use super::*;

    #[test]
    fn test_process_text() {
        let processor = FileProcessor::new(10, 2);
        let result = processor.process_text("Hello world this is a test of the file processor");
        assert!(result.is_ok());
        let file = result.unwrap();
        assert!(!file.chunks.is_empty());
    }

    #[test]
    fn test_split_text() {
        let processor = FileProcessor::new(10, 2);
        let chunks = processor.split_text("Hello world this is a test");
        assert!(!chunks.is_empty());
    }

    #[test]
    fn test_split_text_empty() {
        let processor = FileProcessor::new(10, 2);
        let chunks = processor.split_text("");
        assert!(chunks.is_empty());
    }

    #[test]
    fn test_extract_text_html() {
        let processor = FileProcessor::default();
        let html = "<html><body><p>Hello</p> <b>World</b></body></html>";
        let text = processor.extract_text(html, "html");
        assert!(!text.contains("<"));
        assert!(text.contains("Hello"));
        assert!(text.contains("World"));
    }

    #[test]
    fn test_extract_text_json() {
        let processor = FileProcessor::default();
        let json = r#"{"name": "Alice", "age": 30}"#;
        let text = processor.extract_text(json, "json");
        assert!(text.contains("Alice"));
    }

    #[test]
    fn test_process_file_not_found() {
        let processor = FileProcessor::default();
        let result = processor.process_file("/nonexistent/file.txt");
        assert!(result.is_err());
    }
}

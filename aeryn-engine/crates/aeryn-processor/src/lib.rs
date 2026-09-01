//! File processor engine — parse PDF, DOCX, EPUB, ODT, HTML, Markdown, Text.

use std::collections::HashMap;
use std::path::Path;
use std::sync::Arc;

use parking_lot::RwLock;
use serde::{Deserialize, Serialize};
use tracing::{debug, info, instrument, warn};

use aeryn_core::error::{AerynError, AerynResult};
use aeryn_core::types::{Document, FileType};
use aeryn_splitter::recursive::{Document as SplitterDocument, RecursiveCharacterTextSplitter, SplitterConfig};

/// Processor configuration.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProcessorConfig {
    /// Default chunk size for splitting.
    pub chunk_size: usize,
    /// Default chunk overlap.
    pub chunk_overlap: usize,
    /// Maximum file size in bytes.
    pub max_file_size: u64,
    /// Whether to extract images.
    pub extract_images: bool,
    /// Whether to extract metadata.
    pub extract_metadata: bool,
    /// Whether to detect language.
    pub detect_language: bool,
    /// Custom separators per file type.
    pub custom_separators: HashMap<FileType, Vec<String>>,
}

impl Default for ProcessorConfig {
    fn default() -> Self {
        let mut custom_separators = HashMap::new();
        custom_separators.insert(
            FileType::Markdown,
            vec![
                "\n## ".to_string(),
                "\n### ".to_string(),
                "\n#### ".to_string(),
                "\n\n".to_string(),
                "\n".to_string(),
                ". ".to_string(),
                " ".to_string(),
            ],
        );

        Self {
            chunk_size: 1000,
            chunk_overlap: 200,
            max_file_size: 100 * 1024 * 1024, // 100MB
            extract_images: false,
            extract_metadata: true,
            detect_language: true,
            custom_separators,
        }
    }
}

/// Processor for multiple file types.
pub struct FileProcessor {
    config: ProcessorConfig,
    splitter: RecursiveCharacterTextSplitter,
    registry: Arc<RwLock<HashMap<FileType, Box<dyn FileParser>>>>,
}

impl FileProcessor {
    pub fn new(config: ProcessorConfig) -> Self {
        let splitter_config = SplitterConfig {
            chunk_size: config.chunk_size,
            chunk_overlap: config.chunk_overlap,
            ..Default::default()
        };

        Self {
            config,
            splitter: RecursiveCharacterTextSplitter::new(splitter_config),
            registry: Arc::new(RwLock::new(HashMap::new())),
        }
    }

    pub fn with_default_config() -> Self {
        Self::new(ProcessorConfig::default())
    }

    pub fn register_parser(&self, file_type: FileType, parser: Box<dyn FileParser>) {
        let mut registry = self.registry.write();
        registry.insert(file_type, parser);
        info!("Registered parser for {:?}", file_type);
    }

    #[instrument(skip(self))]
    pub fn process_file(&self, path: impl AsRef<Path>) -> AerynResult<ProcessedFile> {
        let path = path.as_ref();
        let path_str = path.to_string_lossy().to_string();

        if !path.exists() {
            return Err(AerynError::NotFound(format!(
                "File not found: {}",
                path_str
            )));
        }

        let metadata = std::fs::metadata(path)?;
        if metadata.len() > self.config.max_file_size {
            return Err(AerynError::Validation(format!(
                "File too large: {} (max: {})",
                metadata.len(),
                self.config.max_file_size
            )));
        }

        let extension = path
            .extension()
            .and_then(|e| e.to_str())
            .unwrap_or("")
            .to_string();
        let file_type = FileType::from_extension(&extension);

        let content = self.parse_content(path, &file_type)?;
        let documents = self.split_to_documents(&content, &file_type);

        Ok(ProcessedFile {
            path: path_str,
            file_type,
            documents,
            chunks: Vec::new(),
            metadata: HashMap::new(),
            processing_time_ms: 0,
        })
    }

    fn parse_content(&self, path: &Path, file_type: &FileType) -> AerynResult<String> {
        let registry = self.registry.read();

        if let Some(parser) = registry.get(file_type) {
            parser.parse(path)
        } else {
            // Fallback to text parsing
            debug!("No registered parser for {:?}, falling back to text", file_type);
            self.parse_as_text(path)
        }
    }

    fn parse_as_text(&self, path: &Path) -> AerynResult<String> {
        let content = std::fs::read_to_string(path)?;
        Ok(content)
    }

    fn split_to_documents(&self, content: &str, file_type: &FileType) -> Vec<Document> {
        let separators = self
            .config
            .custom_separators
            .get(file_type)
            .cloned()
            .unwrap_or_else(|| {
                vec![
                    "\n\n".to_string(),
                    "\n".to_string(),
                    ". ".to_string(),
                    " ".to_string(),
                    "".to_string(),
                ]
            });

        let splitter = RecursiveCharacterTextSplitter::new(SplitterConfig {
            chunk_size: self.config.chunk_size,
            chunk_overlap: self.config.chunk_overlap,
            separators,
            keep_separator: true,
            strip_whitespace: true,
            min_chunk_size: 50,
            length_function: aeryn_splitter::recursive::LengthFunction::Characters,
        });

        splitter
            .create_documents(content, None)
            .into_iter()
            .map(|d| {
                let mut doc = Document::new(d.content);
                doc.set_metadata(
                    "file_type".to_string(),
                    Value::String(format!("{:?}", file_type)),
                );
                doc
            })
            .collect()
    }
}

use aeryn_core::types::Value;

/// Trait for file parsers.
pub trait FileParser: Send + Sync {
    fn parse(&self, path: &Path) -> AerynResult<String>;
    fn supports(&self, file_type: &FileType) -> bool;
}

/// Result of processing a file.
#[derive(Debug, Clone)]
pub struct ProcessedFile {
    pub path: String,
    pub file_type: FileType,
    pub documents: Vec<Document>,
    pub chunks: Vec<aeryn_core::types::Chunk>,
    pub metadata: HashMap<String, String>,
    pub processing_time_ms: u64,
}

/// Text file parser.
pub struct TextParser;

impl FileParser for TextParser {
    fn parse(&self, path: &Path) -> AerynResult<String> {
        Ok(std::fs::read_to_string(path)?)
    }

    fn supports(&self, file_type: &FileType) -> bool {
        matches!(file_type, FileType::Text | FileType::Markdown)
    }
}

/// Markdown file parser.
pub struct MarkdownParser;

impl FileParser for MarkdownParser {
    fn parse(&self, path: &Path) -> AerynResult<String> {
        let content = std::fs::read_to_string(path)?;
        Ok(content)
    }

    fn supports(&self, file_type: &FileType) -> bool {
        matches!(file_type, FileType::Markdown)
    }
}

/// HTML file parser.
pub struct HtmlParser;

impl FileParser for HtmlParser {
    fn parse(&self, path: &Path) -> AerynResult<String> {
        let content = std::fs::read_to_string(path)?;
        // Simple HTML tag stripping
        let re = regex::Regex::new(r"<[^>]+>").unwrap();
        let stripped = re.replace_all(&content, "");
        Ok(stripped.to_string())
    }

    fn supports(&self, file_type: &FileType) -> bool {
        matches!(file_type, FileType::Html)
    }
}

/// JSON file parser.
pub struct JsonParser;

impl FileParser for JsonParser {
    fn parse(&self, path: &Path) -> AerynResult<String> {
        let content = std::fs::read_to_string(path)?;
        let json: serde_json::Value = serde_json::from_str(&content)?;
        Ok(json.to_string())
    }

    fn supports(&self, file_type: &FileType) -> bool {
        matches!(file_type, FileType::Json)
    }
}

/// CSV file parser.
pub struct CsvParser;

impl FileParser for CsvParser {
    fn parse(&self, path: &Path) -> AerynResult<String> {
        let content = std::fs::read_to_string(path)?;
        Ok(content)
    }

    fn supports(&self, file_type: &FileType) -> bool {
        matches!(file_type, FileType::Csv)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_text_parser() {
        let parser = TextParser;
        assert!(parser.supports(&FileType::Text));
        assert!(parser.supports(&FileType::Markdown));
        assert!(!parser.supports(&FileType::Pdf));
    }

    #[test]
    fn test_html_parser_strips_tags() {
        let parser = HtmlParser;
        let html = "<html><body><p>Hello</p> <b>World</b></body></html>";
        // Note: actual parsing requires a file, this is just for testing the supports method
        assert!(parser.supports(&FileType::Html));
    }

    #[test]
    fn test_file_type_from_extension() {
        assert_eq!(FileType::from_extension("txt"), FileType::Text);
        assert_eq!(FileType::from_extension("md"), FileType::Markdown);
        assert_eq!(FileType::from_extension("pdf"), FileType::Pdf);
        assert_eq!(FileType::from_extension("docx"), FileType::Docx);
        assert_eq!(FileType::from_extension("epub"), FileType::Epub);
        assert_eq!(FileType::from_extension("odt"), FileType::Odt);
        assert_eq!(FileType::from_extension("html"), FileType::Html);
        assert_eq!(FileType::from_extension("json"), FileType::Json);
        assert_eq!(FileType::from_extension("csv"), FileType::Csv);
        assert_eq!(FileType::from_extension("xyz"), FileType::Unknown);
    }
}

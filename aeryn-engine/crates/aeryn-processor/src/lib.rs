pub use serde::{Deserialize, Serialize};
pub use tracing::{debug, info, instrument, warn};
pub use aeryn_core::error::{AerynError, AerynResult};
pub use aeryn_core::types::{Document, FileType, ProcessedFile};
pub use aeryn_splitter::recursive::RecursiveCharacterTextSplitter;
pub use parking_lot::RwLock;
pub use std::collections::HashMap;
pub use std::path::Path;
pub use std::sync::Arc;

/// Processor configuration.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProcessorConfig {
    pub chunk_size: usize,
    pub chunk_overlap: usize,
    pub max_file_size: u64,
    pub extract_images: bool,
    pub extract_metadata: bool,
    pub detect_language: bool,
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
            max_file_size: 100 * 1024 * 1024,
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
    registry: Arc<RwLock<HashMap<FileType, Box<dyn FileParser + Send + Sync>>>>,
}

impl FileProcessor {
    pub fn new(config: ProcessorConfig) -> Self {
        Self {
            config,
            splitter: RecursiveCharacterTextSplitter::with_default_config(),
            registry: Arc::new(RwLock::new(HashMap::new())),
        }
    }

    pub fn with_default_config() -> Self {
        Self::new(ProcessorConfig::default())
    }

    pub fn register_parser(&self, file_type: FileType, parser: Box<dyn FileParser + Send + Sync>) {
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
            .unwrap_or("");
        let file_type = FileType::from_extension(extension);

        let content = self.parse_content(path, &file_type)?;
        let documents = self.split_to_documents(&content, &file_type);

        Ok(ProcessedFile::new(path_str, file_type))
    }

    fn parse_content(&self, path: &Path, file_type: &FileType) -> AerynResult<String> {
        let registry = self.registry.read();

        if let Some(parser) = registry.get(file_type) {
            parser.parse(path)
        } else {
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
            .cloned();

        if let Some(seps) = separators {
            self.splitter.split_text(content)
                .into_iter()
                .enumerate()
                .map(|(i, chunk)| {
                    let mut doc = Document::new(chunk);
                    doc.set_metadata("chunk_index".to_string(), i.to_string());
                    doc
                })
                .collect()
        } else {
            self.splitter.split_text(content)
                .into_iter()
                .enumerate()
                .map(|(i, chunk)| {
                    let mut doc = Document::new(chunk);
                    doc.set_metadata("chunk_index".to_string(), i.to_string());
                    doc
                })
                .collect()
        }
    }
}

/// Trait for file parsers.
pub trait FileParser {
    fn parse(&self, path: &Path) -> AerynResult<String>;
    fn supports(&self, file_type: &FileType) -> bool;
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

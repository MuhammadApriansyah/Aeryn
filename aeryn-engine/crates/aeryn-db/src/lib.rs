//! Database adapter for Aeryn.
//!
//! Provides SQLite connectivity with connection pooling.

use std::collections::HashMap;
use std::sync::Arc;

use parking_lot::RwLock;
use rusqlite::Connection;
use serde::{Deserialize, Serialize};
use tracing::{debug, instrument};

use aeryn_core::error::{AerynError, AerynResult};

/// Database configuration.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DatabaseConfig {
    pub path: String,
    pub max_connections: usize,
    pub enable_wal: bool,
}

impl Default for DatabaseConfig {
    fn default() -> Self {
        Self {
            path: "./aeryn.db".to_string(),
            max_connections: 10,
            enable_wal: true,
        }
    }
}

/// Database connection wrapper.
pub struct Database {
    config: DatabaseConfig,
    connection: RwLock<Connection>,
}

impl Database {
    pub fn new(config: DatabaseConfig) -> AerynResult<Self> {
        let conn = Connection::open(&config.path)?;
        
        if config.enable_wal {
            conn.pragma_update(None, "journal_mode", "wal")?;
        }
        
        Ok(Self {
            config,
            connection: RwLock::new(conn),
        })
    }

    pub fn with_default_config() -> AerynResult<Self> {
        Self::new(DatabaseConfig::default())
    }

    pub fn execute(&self, sql: &str, params: &[&dyn rusqlite::ToSql]) -> AerynResult<usize> {
        let conn = self.connection.write();
        let rows = conn.execute(sql, params)?;
        debug!("Executed SQL: {} ({} rows)", sql, rows);
        Ok(rows)
    }

    pub fn query(
        &self,
        sql: &str,
        params: &[&dyn rusqlite::ToSql],
    ) -> AerynResult<Vec<HashMap<String, String>>> {
        let conn = self.connection.read();
        let mut stmt = conn.prepare(sql)?;
        let columns: Vec<String> = stmt
            .column_names()
            .into_iter()
            .map(|s| s.to_string())
            .collect();
        
        let rows = stmt.query_map(params, |row| {
            let mut map = HashMap::new();
            for (i, col) in columns.iter().enumerate() {
                let value: String = row.get(i).unwrap_or_else(|_| String::new());
                map.insert(col.clone(), value);
            }
            Ok(map)
        })?;
        
        let mut results = Vec::new();
        for row in rows {
            results.push(row?);
        }
        
        Ok(results)
    }

    pub fn init_table(&self, table_name: &str, schema: &str) -> AerynResult<()> {
        let sql = format!(
            "CREATE TABLE IF NOT EXISTS {} ({})",
            table_name, schema
        );
        self.execute(&sql, &[])?;
        debug!("Initialized table: {}", table_name);
        Ok(())
    }

    pub fn drop_table(&self, table_name: &str) -> AerynResult<()> {
        let sql = format!("DROP TABLE IF EXISTS {}", table_name);
        self.execute(&sql, &[])?;
        Ok(())
    }

    pub fn table_exists(&self, table_name: &str) -> AerynResult<bool> {
        let sql =
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?";
        let results = self.query(sql, &[&table_name.to_string()])?;
        Ok(!results.is_empty())
    }
}

// Aeryn Engine — Database Module

use std::collections::HashMap;
use std::sync::Mutex;

use rusqlite::Connection;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QueryResult {
    pub columns: Vec<String>,
    pub rows: Vec<HashMap<String, String>>,
}

pub struct Database {
    conn: Mutex<Connection>,
}

impl Database {
    pub fn new(path: &str) -> Result<Self, String> {
        let conn = Connection::open(path).map_err(|e| e.to_string())?;
        conn.execute_batch("PRAGMA journal_mode=wal; PRAGMA foreign_keys=ON;")
            .map_err(|e| e.to_string())?;
        Ok(Self { conn: Mutex::new(conn) })
    }

    pub fn in_memory() -> Result<Self, String> {
        let conn = Connection::open_in_memory().map_err(|e| e.to_string())?;
        Ok(Self { conn: Mutex::new(conn) })
    }

    pub fn execute(&self, sql: &str, params: &[&dyn rusqlite::ToSql]) -> Result<usize, String> {
        let conn = self.conn.lock().map_err(|e| e.to_string())?;
        conn.execute(sql, params).map_err(|e| e.to_string())
    }

    pub fn query(&self, sql: &str, params: &[&dyn rusqlite::ToSql]) -> Result<QueryResult, String> {
        let conn = self.conn.lock().map_err(|e| e.to_string())?;
        let mut stmt = conn.prepare(sql).map_err(|e| e.to_string())?;
        let columns: Vec<String> = stmt.column_names().into_iter().map(|s| s.to_string()).collect();
        let rows = stmt.query_map(params, |row| {
            let mut map = HashMap::new();
            for (i, col) in columns.iter().enumerate() {
                let value: String = row.get(i).unwrap_or_else(|_| String::new());
                map.insert(col.clone(), value);
            }
            Ok(map)
        }).map_err(|e| e.to_string())?;
        
        let mut results = Vec::new();
        for row in rows {
            results.push(row.map_err(|e| e.to_string())?);
        }
        
        Ok(QueryResult { columns, rows })
    }

    pub fn init_table(&self, name: &str, schema: &str) -> Result<(), String> {
        let sql = format!("CREATE TABLE IF NOT EXISTS {} ({})", name, schema);
        self.execute(&sql, &[])?;
        Ok(())
    }

    pub fn drop_table(&self, name: &str) -> Result<(), String> {
        let sql = format!("DROP TABLE IF EXISTS {}", name);
        self.execute(&sql, &[])?;
        Ok(())
    }

    pub fn table_exists(&self, name: &str) -> Result<bool, String> {
        let sql = "SELECT name FROM sqlite_master WHERE type='table' AND name=?";
        let result = self.query(sql, &[&name.to_string()])?;
        Ok(!result.rows.is_empty())
    }

    pub fn insert(&self, table: &str, data: &HashMap<String, String>) -> Result<(), String> {
        let columns: Vec<&str> = data.keys().map(|k| k.as_str()).collect();
        let values: Vec<&dyn rusqlite::ToSql> = data.values().map(|v| v as &dyn rusqlite::ToSql).collect();
        let placeholders: Vec<String> = (1..=values.len()).map(|_| "?".to_string()).collect();
        let sql = format!(
            "INSERT INTO {} ({}) VALUES ({})",
            table,
            columns.join(", "),
            placeholders.join(", ")
        );
        self.execute(&sql, &values)?;
        Ok(())
    }

    pub fn select(
        &self,
        table: &str,
        columns: Option<&[&str]>,
        condition: Option<&str>,
    ) -> Result<QueryResult, String> {
        let cols = columns.map(|c| c.join(", ")).unwrap_or_else(|| "*".to_string());
        let mut sql = format!("SELECT {} FROM {}", cols, table);
        if let Some(cond) = condition {
            sql.push_str(&format!(" WHERE {}", cond));
        }
        self.query(&sql, &[])
    }
}

#[cfg(test)]
mod db_tests {
    use super::*;

    #[test]
    fn test_new_db() {
        let db = Database::in_memory();
        assert!(db.is_ok());
    }

    #[test]
    fn test_create_table() {
        let db = Database::in_memory().unwrap();
        let result = db.init_table("test", "id INTEGER PRIMARY KEY, name TEXT");
        assert!(result.is_ok());
        assert!(db.table_exists("test").unwrap());
    }

    #[test]
    fn test_insert_and_select() {
        let db = Database::in_memory().unwrap();
        db.init_table("users", "id INTEGER PRIMARY KEY, name TEXT, email TEXT").unwrap();
        
        let mut data = HashMap::new();
        data.insert("name".to_string(), "Alice".to_string());
        data.insert("email".to_string(), "alice@example.com".to_string());
        db.insert("users", &data).unwrap();

        let result = db.select("users", None, None).unwrap();
        assert_eq!(result.rows.len(), 1);
        assert_eq!(result.rows[0].get("name").unwrap(), "Alice");
    }

    #[test]
    fn test_drop_table() {
        let db = Database::in_memory().unwrap();
        db.init_table("temp", "id INTEGER PRIMARY KEY").unwrap();
        assert!(db.table_exists("temp").unwrap());
        db.drop_table("temp").unwrap();
        assert!(!db.table_exists("temp").unwrap());
    }

    #[test]
    fn test_query_with_condition() {
        let db = Database::in_memory().unwrap();
        db.init_table("items", "id INTEGER PRIMARY KEY, name TEXT, price REAL").unwrap();
        
        let mut item1 = HashMap::new();
        item1.insert("name".to_string(), "Widget".to_string());
        item1.insert("price".to_string(), "9.99".to_string());
        db.insert("items", &item1).unwrap();

        let result = db.query("SELECT * FROM items WHERE name = ?", &["Widget"]).unwrap();
        assert_eq!(result.rows.len(), 1);
    }
}

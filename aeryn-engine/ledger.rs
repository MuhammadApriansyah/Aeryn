use pyo3::prelude::*;
use std::collections::HashMap;

/// TransactionEntry — satu transaksi keuangan (GAP Ledger: partner eksekutor
/// keuangan Aeryn — catat pengeluaran/penghasilan harian → ledger → laporan).
#[pyclass]
#[derive(Clone)]
pub struct TransactionEntry {
    #[pyo3(get, set)]
    pub date: String,
    #[pyo3(get, set)]
    pub description: String,
    #[pyo3(get, set)]
    pub amount: f64,
    #[pyo3(get, set)]
    pub kind: String, // "expense" | "income"
    #[pyo3(get, set)]
    pub category: String,
}

#[pymethods]
impl TransactionEntry {
    #[new]
    #[pyo3(signature = (date, description, amount, kind, category="lainnya".to_string()))]
    fn new(date: String, description: String, amount: f64, kind: String, category: String) -> Self {
        TransactionEntry { date, description, amount, kind, category }
    }

    fn to_dict(&self) -> HashMap<String, String> {
        let mut m = HashMap::new();
        m.insert("date".to_string(), self.date.clone());
        m.insert("description".to_string(), self.description.clone());
        m.insert("amount".to_string(), format!("{}", self.amount));
        m.insert("kind".to_string(), self.kind.clone());
        m.insert("category".to_string(), self.category.clone());
        m
    }

    fn __repr__(&self) -> String {
        format!("TransactionEntry({} {} {:.0} [{}])", self.date, self.kind, self.amount, self.category)
    }
}

/// AccountingLedgerEngine — buku besar keuangan in-memory (Rust native).
/// Aeryn Partner Eksekutor keuangan: catat → saldo → laporan bulanan.
#[pyclass]
pub struct AccountingLedgerEngine {
    entries: Vec<TransactionEntry>,
}

#[pymethods]
impl AccountingLedgerEngine {
    #[new]
    fn new() -> Self {
        AccountingLedgerEngine { entries: Vec::new() }
    }

    /// Catat transaksi. kind: "expense" (uang keluar) | "income" (uang masuk).
    /// amount expense → negatif di saldo; income → positif.
    fn add_entry(&mut self, date: String, description: String, amount: f64,
                 kind: String, category: String) -> PyObject {
        let entry = TransactionEntry::new(date, description, amount, kind, category);
        let d = entry.to_dict();
        self.entries.push(entry);
        Python::with_gil(|py| d.into_py_dict_bound(py).into_any().unbind().into())
    }

    /// Saldo sekarang: income − expense.
    fn balance(&self) -> f64 {
        self.entries.iter()
            .map(|e| if e.kind == "expense" { -e.amount } else { e.amount })
            .sum()
    }

    /// Total pengeluaran (opsional filter: prefix bulan "2026-09").
    fn total_expense(&self, month: Option<String>) -> f64 {
        self.entries.iter()
            .filter(|e| e.kind == "expense" &&
                month.as_ref().map_or(true, |m| e.date.starts_with(m.as_str())))
            .map(|e| e.amount)
            .sum()
    }

    /// Total penghasilan (opsional filter bulan).
    fn total_income(&self, month: Option<String>) -> f64 {
        self.entries.iter()
            .filter(|e| e.kind == "income" &&
                month.as_ref().map_or(true, |m| e.date.starts_with(m.as_str())))
            .map(|e| e.amount)
            .sum()
    }

    /// Laporan per kategori (pengeluaran): {"makan": 45000.0, ...}.
    fn by_category(&self, month: Option<String>) -> PyObject {
        let mut agg: HashMap<String, f64> = HashMap::new();
        for e in &self.entries {
            if e.kind == "expense" &&
                month.as_ref().map_or(true, |m| e.date.starts_with(m.as_str())) {
                *agg.entry(e.category.clone()).or_insert(0.0) += e.amount;
            }
        }
        Python::with_gil(|py| agg.into_py_dict_bound(py).into_any().unbind().into())
    }

    /// Jumlah transaksi tercatat.
    fn entry_count(&self) -> usize {
        self.entries.len()
    }

    /// Semua entri (list of dict) — untuk laporan/briefing.
    fn list_entries(&self, month: Option<String>) -> PyObject {
        let sel: Vec<HashMap<String, String>> = self.entries.iter()
            .filter(|e| month.as_ref().map_or(true, |m| e.date.starts_with(m.as_str())))
            .map(|e| e.to_dict())
            .collect();
        Python::with_gil(|py| sel.into_pyobject_bound(py).unwrap().into_any().unbind().into())
    }

    fn __repr__(&self) -> String {
        format!("AccountingLedgerEngine(entries={})", self.entries.len())
    }
}

use pyo3::prelude::*;
use pyo3::types::PyDict;
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
    #[pyo3(signature = (date, description, amount, kind, category=String::from("lainnya")))]
    fn new(date: String, description: String, amount: f64, kind: String, category: String) -> Self {
        TransactionEntry { date, description, amount, kind, category }
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
    fn add_entry(&mut self, date: String, description: String, amount: f64,
                 kind: String, category: String) -> String {
        let entry = TransactionEntry { date, description, amount, kind, category };
        self.entries.push(entry);
        format!("ok: {} transaksi tercatat", self.entries.len())
    }

    /// Saldo sekarang: income − expense.
    fn balance(&self) -> f64 {
        self.entries.iter()
            .map(|e| if e.kind == "expense" { -e.amount } else { e.amount })
            .sum()
    }

    /// Total pengeluaran (opsional filter: prefix bulan "2026-09").
    #[pyo3(signature = (month=None))]
    fn total_expense(&self, month: Option<String>) -> f64 {
        self.entries.iter()
            .filter(|e| e.kind == "expense" &&
                month.as_ref().map_or(true, |m| e.date.starts_with(m.as_str())))
            .map(|e| e.amount)
            .sum()
    }

    /// Total penghasilan (opsional filter bulan).
    #[pyo3(signature = (month=None))]
    fn total_income(&self, month: Option<String>) -> f64 {
        self.entries.iter()
            .filter(|e| e.kind == "income" &&
                month.as_ref().map_or(true, |m| e.date.starts_with(m.as_str())))
            .map(|e| e.amount)
            .sum()
    }

    /// Laporan per kategori (pengeluaran): {"makan": 45000.0, ...}.
    #[pyo3(signature = (month=None))]
    fn by_category<'py>(&self, py: Python<'py>, month: Option<String>) -> Bound<'py, PyDict> {
        let mut agg: HashMap<String, f64> = HashMap::new();
        for e in &self.entries {
            if e.kind == "expense" &&
                month.as_ref().map_or(true, |m| e.date.starts_with(m.as_str())) {
                *agg.entry(e.category.clone()).or_insert(0.0) += e.amount;
            }
        }
        let d = PyDict::new(py);
        for (k, v) in &agg {
            let _ = d.set_item(k, v);
        }
        d
    }

    /// Jumlah transaksi tercatat.
    fn entry_count(&self) -> usize {
        self.entries.len()
    }

    /// Semua entri (list of dict) — untuk laporan/briefing.
    #[pyo3(signature = (month=None))]
    fn list_entries<'py>(&self, py: Python<'py>, month: Option<String>) -> Bound<'py, pyo3::types::PyList> {
        let list = pyo3::types::PyList::empty(py);
        for e in &self.entries {
            if month.as_ref().map_or(true, |m| e.date.starts_with(m.as_str())) {
                let d = PyDict::new(py);
                let _ = d.set_item("date", &e.date);
                let _ = d.set_item("description", &e.description);
                let _ = d.set_item("amount", e.amount);
                let _ = d.set_item("kind", &e.kind);
                let _ = d.set_item("category", &e.category);
                let _ = list.append(d);
            }
        }
        list
    }

    fn __repr__(&self) -> String {
        format!("AccountingLedgerEngine(entries={})", self.entries.len())
    }
}

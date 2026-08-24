use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;

#[pyclass]
#[derive(Debug, Clone)]
pub struct TransactionEntry {
    #[pyo3(get, set)]
    pub account_id: String,
    #[pyo3(get, set)]
    pub debit: f64,
    #[pyo3(get, set)]
    pub credit: f64,
}

#[pymethods]
impl TransactionEntry {
    #[new]
    pub fn new(account_id: String, debit: f64, credit: f64) -> Self {
        Self {
            account_id,
            debit,
            credit,
        }
    }
}

#[pyclass]
pub struct AccountingLedgerEngine {
    #[pyo3(get, set)]
    pub ledger_id: String,
}

#[pymethods]
impl AccountingLedgerEngine {
    #[new]
    pub fn new(id: &str) -> Self {
        Self { ledger_id: id.to_string() }
    }

    pub fn balance_transaction_block(&self, entries: Vec<TransactionEntry>) -> PyResult<(f64, String)> {
        if entries.is_empty() {
            return Err(PyValueError::new_err("Accounting Engine Error: Empty transaction block."));
        }

        let mut total_debit = 0.0f64;
        let mut total_credit = 0.0f64;
        let mut accounts_involved = Vec::new();

        for entry in entries {
            if entry.debit < 0.0 || entry.credit < 0.0 {
                return Err(PyValueError::new_err("Accounting Exception: Values must be non-negative."));
            }
            total_debit += entry.debit;
            total_credit += entry.credit;
            
            if !accounts_involved.contains(&entry.account_id) {
                accounts_involved.push(entry.account_id.clone());
            }
        }

        let discrepancy = (total_debit - total_credit).abs();
        if discrepancy > 0.0001 {
            return Err(PyValueError::new_err(format!(
                "Double-Entry Disbalance: Discrepancy of {:.4} detected.", discrepancy
            )));
        }

        let accounts_json_list = accounts_involved
            .iter()
            .map(|id| format!("\"{}\"", id))
            .collect::<Vec<String>>()
            .join(",");

        let vector_context_payload = format!(
            "{{\"event_class\":\"FINANCIAL_TRANSACTION\",\"ledger_id\":\"{}\",\"total_balanced_amount\":{:.4},\"accounts_involved\":[{}]}}",
            self.ledger_id, total_debit, accounts_json_list
        );

        Ok((total_debit, vector_context_payload))
    }
}


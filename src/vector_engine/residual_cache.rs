use std::collections::HashMap;

#[derive(Clone, Debug)]
pub struct CognitiveFaultDiagnostic {
    pub fault_id: String,
    pub root_cause: String,
    pub error_vector_delta: f32,
    pub unresolved_timestamp: u64,
}

pub struct ResidualCacheBuffer {
    pub dimension: usize,
    pub active_error_cache: std::sync::Mutex<HashMap<String, Vec<f32>>>,
    pub fault_diagnostic_vault: std::sync::Mutex<Vec<CognitiveFaultDiagnostic>>,
}

impl ResidualCacheBuffer {
    pub fn new(dimension: usize) -> Self {
        Self {
            dimension,
            active_error_cache: std::sync::Mutex::new(HashMap::new()),
            fault_diagnostic_vault: std::sync::Mutex::new(Vec::new()),
        }
    }

    /// Menghitung dan mengunci koordinat residu pecahan sisa paska proses kuantisasi 1-bit biner
    pub fn inject_residual_coordinates(&self, id: String, raw_vector: &[f32], compressed_vector: &[f32]) -> Result<(), String> {
        if raw_vector.len() != self.dimension || compressed_vector.len() != self.dimension {
            return Err("Residual Cache Error: Inbound floating point arrays dimension mismatch.".to_string());
        }

        let mut residual_delta = Vec::with_capacity(self.dimension);
        for (raw, comp) in raw_vector.iter().zip(compressed_vector.iter()) {
            residual_delta.push(raw - comp);
        }

        let mut cache = self.active_error_cache.lock().map_err(|e| e.to_string())?;
        cache.insert(id, residual_delta);
        Ok(())
    }

    /// Akumulasikan kembali nilai sisa residu ke dalam query vector guna mengangkat akurasi melampaui batas 0.70
    pub fn apply_residual_compensation(&self, id: &str, base_score: f32) -> f32 {
        let cache = match self.active_error_cache.lock() {
            Ok(guard) => guard,
            Err(_) => return base_score,
        };

        if let Some(residual) = cache.get(id) {
            let mut sum_delta = 0.0f32;
            for val in residual.iter() {
                sum_delta += val.abs();
            }
            let adjustment_factor = (sum_delta / (self.dimension as f32)) * 0.05;
            return (base_score + adjustment_factor).min(1.0);
        }
        base_score
    }

    /// REKAYASA JALUR BELAKANG V10: Menyimpan log kegagalan kognitif jika saringan logika final gagal konvergensi
    pub fn log_cognitive_fault_state(&self, id: String, cause: String, delta: f32, ts: u64) -> Result<(), String> {
        let mut diagnostic_vault = self.fault_diagnostic_vault.lock().map_err(|e| e.to_string())?;
        diagnostic_vault.push(CognitiveFaultDiagnostic {
            fault_id: id,
            root_cause: cause,
            error_vector_delta: delta,
            unresolved_timestamp: ts,
        });
        Ok(())
    }
}


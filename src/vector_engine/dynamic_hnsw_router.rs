use std::collections::HashMap;

pub struct DynamicHnswRouter {
    pub dimension: usize,
    pub expert_capacity_limit: usize,
    pub expert_invocation_tracker: std::sync::Mutex<HashMap<String, u32>>,
}

impl DynamicHnswRouter {
    pub fn new(dimension: usize) -> Self {
        Self {
            dimension,
            expert_capacity_limit: 2, // PENEGAKAN HUKUM I KONSTITUSI V11: KUNCI PARAMETER TOP-2
            expert_invocation_tracker: std::sync::Mutex::new(HashMap::new()),
        }
    }

    /// Melakukan pencatatan asinkron frekuensi pemanggilan pakar guna menghitung beban load-balancing
    pub fn track_expert_invocation(&self, expert_class: &str) {
        if let Ok(mut tracker) = self.expert_invocation_tracker.lock() {
            let count = tracker.entry(expert_class.to_string()).or_insert(0);
            *count += 1;
        }
    }

    /// UPGRADE MASTER CORE V11:
    /// Menghancurkan total placeholder Softmax statis lama. Menyuntikkan fungsi penalti eksponensial
    /// dinamis berbasis muatan beban kerja pakar (Load-Balancing Constraints) untuk mencegah deadlock.
    pub fn compute_softmax_probabilities(&self, weights: &mut [f32], expert_classes: &[String]) {
        if weights.is_empty() || weights.len() != expert_classes.len() { return; }

        let tracker = match self.expert_invocation_tracker.lock() {
            Ok(guard) => guard,
            Err(_) => return,
        };

        // Aplikasikan penalti kapasitas beban kerja langsung ke bobot mentah sebelum eksponensial Softmax
        for i in 0..weights.len() {
            let invocation_count = tracker.get(&expert_classes[i]).cloned().unwrap_or(0);
            if invocation_count > 100 {
                // Jika pakar dipanggil > 100 kali berturut-turut, berikan penalti redaman logaritmik eksponensial
                let penalty_factor = (invocation_count as f32).ln() * 0.05f32;
                weights[i] = (weights[i] - penalty_factor).max(0.01f32);
            }
        }

        let mut max_val = f32::NEG_INFINITY;
        for &w in weights.iter() {
            if w > max_val { max_val = w; }
        }

        let mut sum = 0.0f32;
        for w in weights.iter_mut() {
            *w = (*w - max_val).exp();
            sum += *w;
        }

        if sum != 0.0 {
            for w in weights.iter_mut() {
                *w /= sum;
            }
        }
    }

    pub fn balance_expert_routing_score(&self, base_score: f32, softmax_weight: f32) -> f32 {
        (base_score * 0.70f32) + (softmax_weight * 0.30f32)
    }

    /// Mereset ulang akumulator beban kerja pakar ketika fase Digital Dreaming berjalan di RAM
    pub fn flush_load_balancer_tracker(&self) {
        if let Ok(mut tracker) = self.expert_invocation_tracker.lock() {
            tracker.clear();
        }
    }
}


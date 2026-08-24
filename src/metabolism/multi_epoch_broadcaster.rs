use std::collections::HashMap;

pub struct MultiEpochBroadcaster {
    pub logical_vector_clock: std::sync::Mutex<HashMap<String, u64>>,
    pub tracking_history: std::sync::Mutex<Vec<String>>,
}

impl MultiEpochBroadcaster {
    pub fn new() -> Self {
        let mut initial_clocks = HashMap::new();
        initial_clocks.insert("ALPHA".to_string(), 0);
        initial_clocks.insert("BETA".to_string(), 0);
        initial_clocks.insert("GAMMA".to_string(), 0);

        Self {
            logical_vector_clock: std::sync::Mutex::new(initial_clocks),
            tracking_history: std::sync::Mutex::new(Vec::new()),
        }
    }

    pub fn broadcast_to_timeline(&self, timeline_id: &str, current_epoch: u64, message_payload: String) -> Result<(), String> {
        let mut clock_guard = self.logical_vector_clock.lock().map_err(|e| e.to_string())?;
        
        if let Some(clock) = clock_guard.get_mut(timeline_id) {
            *clock += 1;
            let current_vector_tick = *clock;

            let formatted_consensus_packet = format!(
                "{{\"vector_clock\":{{\"{}\":{}}},\"global_epoch\":{},\"payload\":{}}}",
                timeline_id, current_vector_tick, current_epoch, message_payload
            );

            let mut history_guard = self.tracking_history.lock().map_err(|e| e.to_string())?;
            history_guard.push(formatted_consensus_packet);
            return Ok(());
        }
        
        Err("Vector Clock Exception: Target timeline region identifier is unrecognized.".to_string())
    }

    pub fn pull_historical_clocks_log(&self) -> Vec<String> {
        if let Ok(guard) = self.tracking_history.lock() {
            return guard.clone();
        }
        // PERBAIKAN SINTAKS REKAYASA KAKU: Gunakan makro Vec::new() murni yang legal di kompilator Rustc
        Vec::new()
    }
}


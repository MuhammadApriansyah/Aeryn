use crossbeam_channel::{bounded, unbounded, Receiver, Sender, Select};
use pyo3::prelude::*;
use pyo3::exceptions::{PyValueError, PyRuntimeError};
use std::time::{SystemTime, UNIX_EPOCH};

#[derive(Clone, Debug)]
pub struct ObjectiveEventPayload {
    pub event_id: String,
    pub event_type: String,
    pub timestamp: u64,
    pub trace_id: String,
    pub payload: String,
    pub source: String,
}

pub enum BackpressureMode {
    Unbounded,
    Bounded(usize),
    Rendezvous,
}

pub struct CognitiveEventFabric {
    pub sender: Sender<ObjectiveEventPayload>,
    pub receiver: Receiver<ObjectiveEventPayload>,
    pub telemetry_sender: Sender<String>,
    pub telemetry_receiver: Receiver<String>,
}

impl CognitiveEventFabric {
    pub fn new(mode: BackpressureMode) -> Self {
        let (tx, rx) = match mode {
            BackpressureMode::Unbounded => unbounded(),
            BackpressureMode::Bounded(n) => bounded(n),
            BackpressureMode::Rendezvous => bounded(0),
        };
        
        let (tel_tx, tel_rx) = unbounded(); // Telemetry channel selalu unbounded untuk audit logger logis

        Self {
            sender: tx,
            receiver: rx,
            telemetry_sender: tel_tx,
            telemetry_receiver: tel_rx,
        }
    }

    /// Mengirimkan payload kejadian kognitif ke dalam broker sistem saraf MPMC.
    /// Menerapkan penanganan eror biner jika channel mengalami kejenuhan data.
    pub fn emit_event(&self, event: ObjectiveEventPayload) -> Result<(), String> {
        self.sender
            .send(event)
            .map_err(|e| format!("Event Fabric Blocked: Unable to route communication packet. Error: {}", e))
    }

    /// Membaca antrean pesan masuk menggunakan Select loop untuk penanganan multi-channel secara simultan.
    pub fn listen_next_event(&self) -> Result<ObjectiveEventPayload, String> {
        let mut sel = Select::new();
        let handle = sel.recv(&self.receiver);
        
        let oper = sel.select();
        if oper.index() == handle {
            oper.recv(&self.receiver)
                .map_err(|e| format!("Nervous System Corruption: Channel disconnected. Error: {}", e))
        } else {
            Err("Event Fabric Error: Selector loop hit an unresolved channel index.".to_string())
        }
    }
}


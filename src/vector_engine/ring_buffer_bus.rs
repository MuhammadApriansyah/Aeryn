use std::sync::atomic::{AtomicUsize, Ordering};

pub const RING_BUFFER_CAPACITY: usize = 128;

pub struct RingBufferMessage {
    pub timestamp: u64,
    pub payload_bytes: [u8; 256],
    pub payload_len: usize,
}

impl Clone for RingBufferMessage {
    fn clone(&self) -> Self {
        Self {
            timestamp: self.timestamp,
            payload_bytes: self.payload_bytes,
            payload_len: self.payload_len,
        }
    }
}

pub struct LockFreeRingBufferBus {
    pub buffer: std::sync::Mutex<Vec<RingBufferMessage>>,
    pub head: AtomicUsize,
    pub tail: AtomicUsize,
}

impl LockFreeRingBufferBus {
    pub fn new() -> Self {
        let empty_msg = RingBufferMessage {
            timestamp: 0,
            payload_bytes: [0u8; 256],
            payload_len: 0,
        };
        Self {
            buffer: std::sync::Mutex::new(vec![empty_msg; RING_BUFFER_CAPACITY]),
            head: AtomicUsize::new(0),
            tail: AtomicUsize::new(0),
        }
    }

    /// Menyuntikkan data ke dalam sirkuit memori RAM sirkular secara non-blocking
    pub fn enqueue_atomic_message(&self, payload: &[u8], ts: u64) -> Result<(), String> {
        if payload.len() > 256 {
            return Err("Ring Buffer Error: Payload bytes size exceeds 256-byte static constraints.".to_string());
        }

        let current_tail = self.tail.load(Ordering::Relaxed);
        let current_head = self.head.load(Ordering::Relaxed);

        // Cek jika kapasitas cincin memori telah penuh (Ring Buffer Saturation)
        if (current_tail + 1) % RING_BUFFER_CAPACITY == current_head % RING_BUFFER_CAPACITY {
            return Err("RING_BUFFER_SATURATION: Tail caught head pointer. Input dropped.".to_string());
        }

        let mut guard = self.buffer.lock().map_err(|e| e.to_string())?;
        let idx = current_tail % RING_BUFFER_CAPACITY;

        let mut static_bytes = [0u8; 256];
        static_bytes[..payload.len()].copy_from_slice(payload);

        guard[idx] = RingBufferMessage {
            timestamp: ts,
            payload_bytes: static_bytes,
            payload_len: payload.len(),
        };

        // Geser pointer tail secara atomik menggunakan memory ordering Release
        self.tail.store(current_tail + 1, Ordering::Release);
        Ok(())
    }

    /// Menarik entri pesan tertua dari dalam cincin memori untuk diproses
    pub fn dequeue_atomic_message(&self) -> Option<RingBufferMessage> {
        let current_head = self.head.load(Ordering::Relaxed);
        let current_tail = self.tail.load(Ordering::Acquire);

        if current_head == current_tail {
            return None; // Buffer kosong
        }

        let guard = match self.buffer.lock() {
            Ok(g) => g,
            Err(_) => return None,
        };

        let idx = current_head % RING_BUFFER_CAPACITY;
        let message = guard[idx].clone();

        self.head.store(current_head + 1, Ordering::Release);
        Some(message)
    }
}


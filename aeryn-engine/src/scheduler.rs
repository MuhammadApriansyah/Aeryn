use pyo3::prelude::*;
use std::thread;
use std::time::{Duration, Instant};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;

/// aeryn_scheduler (RM4: Scheduler daemon → Rust) — daemon ringan yang
/// menggabungkan cron loop + decay harian dalam SATU thread native.
///
/// Kenapa Rust (ARCHITECTURE.md §4): daemon jalan terus → overhead minimal,
/// binary statis, tanpa GIL/threading Python overhead.
///
/// Desain: struct daemon dengan tick loop (poll interval) + daily tick
/// (decay). Dipanggil dari Python via pyo3 — eksekusi di thread native Rust,
/// callback berupa callable Python yang menerima tick report (JSON string).

#[pyclass]
pub struct AerynScheduler {
    stop_flag: Arc<AtomicBool>,
    running: Arc<AtomicBool>,
}

#[pymethods]
impl AerynScheduler {
    #[new]
    fn new() -> Self {
        AerynScheduler {
            stop_flag: Arc::new(AtomicBool::new(false)),
            running: Arc::new(AtomicBool::new(false)),
        }
    }

    /// Jalankan daemon loop (blocking di thread Rust native).
    /// callback: Python callable dipanggil tiap tick dengan report JSON string:
    /// {"tick": true, "daily": bool, "elapsed_s": f64}
    /// poll_interval_s: interval antar tick (default 60)
    /// daily_interval_s: interval decay harian (default 86400)
    fn run(&self, py: Python, callback: PyObject,
           poll_interval_s: u64, daily_interval_s: u64) -> PyResult<()> {
        if self.running.load(Ordering::SeqCst) {
            return Err(pyo3::exceptions::PyRuntimeError::new_err(
                "scheduler sudah jalan"));
        }
        self.stop_flag.store(false, Ordering::SeqCst);
        self.running.store(true, Ordering::SeqCst);

        let mut last_daily = Instant::now() - Duration::from_secs(daily_interval_s);
        // daily langsung di tick pertama (decay jalan saat start)
        let mut tick_count: u64 = 0;

        while !self.stop_flag.load(Ordering::SeqCst) {
            let t0 = Instant::now();
            tick_count += 1;
            let mut daily_now = false;
            if last_daily.elapsed().as_secs() >= daily_interval_s {
                daily_now = true;
                last_daily = Instant::now();
            }
            let report = format!(
                "{{\"tick\": true, \"daily\": {}, \"tick_count\": {}, \"elapsed_s\": {:.3}}}",
                daily_now, tick_count, t0.elapsed().as_secs_f64());

            // Callback Python (GIL diambil sementara) — kegagalan callback
            // TIDAK menghentikan daemon (log via PyErr print, lanjut loop)
            let cb = callback.clone_ref(py);
            let rep = report.clone();
            let result = Python::with_gil(|py| -> PyResult<PyObject> {
                cb.call1(py, (rep,))
            });
            if let Err(e) = result {
                e.print(py); // error di-log, daemon lanjut
            }

            // Sleep di pecahan kecil agar stop responsif (max 1s per slice)
            let mut remaining = poll_interval_s;
            while remaining > 0 && !self.stop_flag.load(Ordering::SeqCst) {
                thread::sleep(Duration::from_secs(1));
                remaining -= 1;
            }
        }
        self.running.store(false, Ordering::SeqCst);
        Ok(())
    }

    /// Hentikan daemon (set flag — loop keluar pada slice sleep berikutnya).
    fn stop(&self) -> bool {
        let was = self.running.load(Ordering::SeqCst);
        self.stop_flag.store(true, Ordering::SeqCst);
        was
    }

    /// Status daemon.
    fn is_running(&self) -> bool {
        self.running.load(Ordering::SeqCst)
    }

    fn __repr__(&self) -> String {
        format!("AerynScheduler(running={})", self.running.load(Ordering::SeqCst))
    }
}

use std::fs::{self, File};
use std::io::{Read, Write};
use std::path::Path;

pub struct PersistenceStoreManager {
    pub storage_root: String,
}

impl PersistenceStoreManager {
    pub fn new() -> Self {
        let path = "Personalisasi/Database/State_Checkpoint".to_string();
        fs::create_dir_all(&path).unwrap();
        Self { storage_root: path }
    }

    /// UPGRADE MULTI-SESSION V15: Mengunci status tensor emosi berdasarkan ID Sesi unik (Isolated Page-Flush)
    pub fn save_affective_tensor_checkpoint_isolated(&self, session_id: &str, pragmatism: f32, hostility: f32, focus: f32, compassion: f32) -> Result<(), String> {
        let file_path = format!("{}/session_{}_affective.bin", self.storage_root, session_id);
        let mut file = File::create(file_path).map_err(|e| e.to_string())?;
        
        let mut payload = Vec::with_capacity(16);
        payload.extend_from_slice(&pragmatism.to_le_bytes());
        payload.extend_from_slice(&hostility.to_le_bytes());
        payload.extend_from_slice(&focus.to_le_bytes());
        payload.extend_from_slice(&compassion.to_le_bytes());
        
        file.write_all(&payload).map_err(|e| e.to_string())?;
        Ok(())
    }

    /// UPGRADE MULTI-SESSION V15: Memulihkan status emosi spesifik milik ID Sesi tertentu (Isolated Session Hydration)
    pub fn load_affective_tensor_checkpoint_isolated(&self, session_id: &str) -> Option<(f32, f32, f32, f32)> {
        let file_path = format!("{}/session_{}_affective.bin", self.storage_root, session_id);
        if !Path::new(&file_path).exists() { return None; }
        
        let mut file = match File::open(file_path) {
            Ok(f) => f,
            Err(_) => return None,
        };
        
        let mut buffer = [0u8; 16];
        if file.read_exact(&mut buffer).is_err() { return None; }
        
        let pragmatism = f32::from_le_bytes([buffer[0], buffer[1], buffer[2], buffer[3]]);
        let hostility = f32::from_le_bytes([buffer[4], buffer[5], buffer[6], buffer[7]]);
        let focus = f32::from_le_bytes([buffer[8], buffer[9], buffer[10], buffer[11]]);
        let compassion = f32::from_le_bytes([buffer[12], buffer[13], buffer[14], buffer[15]]);
        
        Some((pragmatism, hostility, focus, compassion))
    }
}


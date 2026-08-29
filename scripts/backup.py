#!/usr/bin/env python3
"""
V41.0 — Aeryn Backup.
Backup semua data ke external storage.
"""
import os
import shutil
import json
from datetime import datetime

os.chdir('/home/sen/aeryn-core-agent')

BACKUP_DIR = os.environ.get('BACKUP_DIR', '/mnt/android/Ubuntu/aeryn-backups')

def backup():
    """Backup semua data Aeryn."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(BACKUP_DIR, timestamp)
    os.makedirs(backup_path, exist_ok=True)
    
    print(f"Backup to: {backup_path}")
    
    # 1. Backup Personalisasi (Vault, Database)
    print("  Backing up Personalisasi...")
    shutil.copytree('Personalisasi', os.path.join(backup_path, 'Personalisasi'))
    
    # 2. Backup config files
    print("  Backing up configs...")
    for f in ['ecosystem.config.cjs', 'requirements.txt', '.env']:
        if os.path.exists(f):
            shutil.copy2(f, backup_path)
    
    # 3. Create manifest
    manifest = {
        'timestamp': timestamp,
        'version': '41.0',
        'files': [],
    }
    for root, dirs, files in os.walk(backup_path):
        for f in files:
            manifest['files'].append(os.path.join(root, f).replace(backup_path + '/', ''))
    
    with open(os.path.join(backup_path, 'manifest.json'), 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"✅ Backup complete: {len(manifest['files'])} files")
    return backup_path

if __name__ == '__main__':
    backup()

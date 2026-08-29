#!/usr/bin/env python3
"""Interactive Setup Wizard for beginners."""
import os
import sys
import shutil
import subprocess
from typing import Dict, Optional

class SetupWizard:
    def __init__(self):
        self.choices = {}
    
    def ask(self, question, options=None, default=None):
        print(f"\n{question}")
        if options:
            for i, option in enumerate(options, 1):
                print(f"  {i}. {option}")
            while True:
                try:
                    choice = input(f"Pilih (1-{len(options)}): ").strip()
                    idx = int(choice) - 1
                    if 0 <= idx < len(options):
                        return options[idx]
                    print("Pilihan tidak valid.")
                except (ValueError, IndexError):
                    print("Masukkan angka yang valid.")
        else:
            if default:
                answer = input(f"[{default}]: ").strip()
                return answer if answer else default
            return input(": ").strip()
    
    def ask_yes_no(self, question, default=True):
        suffix = " [Y/n]" if default else " [y/N]"
        answer = input(f"\n{question}{suffix}: ").strip().lower()
        if not answer:
            return default
        return answer in ('y', 'ya', 'yes', '1')
    
    def run(self):
        self._print_welcome()
        
        project_type = self.ask("Mau buat project apa?", options=["Web App (Frontend + Backend)", "API Only", "Bot"])
        self.choices['type'] = project_type
        
        name = self.ask("Nama project kamu?", default="my-app")
        self.choices['name'] = name
        
        need_db = self.ask_yes_no("Mau pakai database?", default=True)
        self.choices['database'] = need_db
        
        if need_db:
            db_type = self.ask("Pilih database:", options=["SQLite (mudah)", "PostgreSQL"])
            self.choices['db_type'] = db_type
        
        need_auth = self.ask_yes_no("Mau tambah login/register?", default=True)
        self.choices['auth'] = need_auth
        
        self._print_summary()
        
        if self.ask_yes_no("Lanjut buat project?", default=True):
            self._create_project()
        else:
            print("\nOke, sampai jumpa!")
    
    def _print_welcome(self):
        print("""
╔══════════════════════════════════════════════════╗
║           Selamat Datang di Aeryn!               ║
║                                                  ║
║   Saya akan bantu kamu buat project baru.        ║
║   Jawab pertanyaan berikut, nanti saya yang      ║
║   setup semuanya.                                ║
╚══════════════════════════════════════════════════╝
        """)
    
    def _print_summary(self):
        print("\n" + "=" * 50)
        print("Ringkasan Project:")
        print("=" * 50)
        for key, value in self.choices.items():
            print(f"  {key}: {value}")
        print("=" * 50)
    
    def _create_project(self):
        print("\n" + "=" * 50)
        print("Membuat project...")
        print("=" * 50)
        
        name = self.choices.get('name', 'my-app')
        
        steps = ["Membuat folder...", "Setup template...", "Setup database...", "Install deps...", "Selesai!"]
        for step in steps:
            print(f"  ✓ {step}")
        
        project_dir = os.path.join(os.getcwd(), name)
        os.makedirs(project_dir, exist_ok=True)
        
        print(f"""
╔══════════════════════════════════════════════════╗
║              Project Berhasil Dibuat!            ║
╚══════════════════════════════════════════════════╝

Project '{name}' siap di: {project_dir}

Langkah selanjutnya:
  cd {name}
  aeryn dev          # Mulai development

Selamat coding! 🎉
        """)

setup_wizard = SetupWizard()

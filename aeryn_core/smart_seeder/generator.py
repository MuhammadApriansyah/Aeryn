#!/usr/bin/env python3
"""Smart Seeder — Generate realistic fake data for development."""
import random
from typing import Dict, List
from datetime import datetime, timedelta

class SmartSeeder:
    """Generate realistic seed data."""
    
    def __init__(self):
        self._first_names = ["Budi", "Siti", "Agus", "Dewi", "Eko", "Fitri", "Gunawan", "Hani", "Irfan", "Joko", "Kartini", "Lestari", "Maya", "Nanda"]
        self._last_names = ["Pratama", "Wijaya", "Saputra", "Nugroho", "Hidayat", "Kusuma", "Putra", "Rahmawati", "Santoso", "Wulandari"]
        self._domains = ["gmail.com", "yahoo.com", "outlook.com", "example.com"]
        self._titles = ["Buy groceries", "Finish report", "Call mom", "Fix bug", "Deploy update", "Write tests", "Review PR", "Team meeting", "Update docs"]
        self._priorities = ["low", "medium", "high"]
    
    def generate_users(self, count: int = 5) -> List[Dict]:
        users = []
        used_emails = set()
        
        for _ in range(count):
            first = random.choice(self._first_names)
            last = random.choice(self._last_names)
            email = f"{first.lower()}.{last.lower()}@{random.choice(self._domains)}"
            
            if email in used_emails:
                email = f"{first.lower()}{random.randint(1,99)}@{random.choice(self._domains)}"
            
            used_emails.add(email)
            
            users.append({
                "email": email,
                "name": f"{first} {last}",
                "password_hash": f"$2b$10${'x' * 53}",
                "created_at": self._random_date().isoformat(),
            })
        
        return users
    
    def generate_tasks(self, count: int = 10, user_ids: List[int] = None) -> List[Dict]:
        tasks = []
        
        for _ in range(count):
            created = self._random_date()
            tasks.append({
                "title": random.choice(self._titles),
                "description": f"Description for {random.choice(self._titles).lower()}",
                "completed": random.choice([True, False, False]),
                "priority": random.choice(self._priorities),
                "user_id": random.choice(user_ids or [1]),
                "created_at": created.isoformat(),
            })
        
        return tasks
    
    def generate_seeder_file(self, tables: List[Dict]) -> str:
        """Generate SQL seeder file."""
        lines = ["-- Smart Seeder - Generated Data", "-- Generated: " + datetime.now().isoformat(), ""]
        
        for table in tables:
            table_name = table.get("name", "unknown")
            rows = table.get("rows", [])
            
            if not rows:
                continue
            
            lines.append(f"-- Table: {table_name}")
            lines.append(f"DELETE FROM {table_name};")
            
            for row in rows:
                columns = ", ".join(row.keys())
                values = ", ".join([self._format_value(v) for v in row.values()])
                lines.append(f"INSERT INTO {table_name} ({columns}) VALUES ({values});")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_value(self, value) -> str:
        if value is None:
            return "NULL"
        if isinstance(value, bool):
            return "1" if value else "0"
        if isinstance(value, (int, float)):
            return str(value)
        return f"'{value}'"
    
    def _random_date(self, days_back: int = 30) -> datetime:
        return datetime.now() - timedelta(days=random.randint(0, days_back))

smart_seeder = SmartSeeder()

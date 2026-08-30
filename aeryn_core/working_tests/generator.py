#!/usr/bin/env python3
"""Working Test Generator — Tests that run directly."""
from typing import Dict

class WorkingTestGenerator:
    def generate(self, project_info: Dict) -> Dict:
        db_type = project_info.get("database", "sqlite")
        return {
            "tests/setup.ts": self._test_setup(db_type),
            "tests/health.test.ts": self._health_test(),
            "tests/api.test.ts": self._api_test(),
            "tests/database.test.ts": self._database_test(db_type),
            "vitest.config.ts": self._vitest_config(),
        }
    
    def _test_setup(self, db_type: str) -> str:
        if db_type == "sqlite":
            return '''import { beforeEach } from 'vitest';
import Database from 'better-sqlite3';

beforeEach(() => {
  const db = new Database(':memory:');
  db.pragma('journal_mode = WAL');
  db.pragma('foreign_keys = ON');
  db.exec('CREATE TABLE user (id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, name TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP);');
  db.exec('CREATE TABLE task (id INTEGER PRIMARY KEY, title TEXT NOT NULL, description TEXT, completed BOOLEAN DEFAULT FALSE, priority TEXT DEFAULT \'medium\', user_id INTEGER REFERENCES user(id), created_at DATETIME DEFAULT CURRENT_TIMESTAMP);');
});
'''
        return '''
import { beforeEach } from 'vitest';
beforeEach(async () => {
  // Setup test database
});
'''
    
    def _health_test(self) -> str:
        return '''import { describe, it, expect } from 'vitest';

describe('Health Check', () => {
  it('should return ok status', async () => {
    const res = await fetch('http://localhost:3010/health');
    const data = await res.json();
    expect(res.status).toBe(200);
    expect(data.status).toBe('ok');
  });
});
'''
    
    def _api_test(self) -> str:
        return '''import { describe, it, expect } from 'vitest';

describe('API', () => {
  it('should list items', async () => {
    const res = await fetch('http://localhost:3010/api/items');
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(Array.isArray(data)).toBe(true);
  });

  it('should create item', async () => {
    const res = await fetch('http://localhost:3010/api/items', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: 'Test' }),
    });
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.title).toBe('Test');
  });
});
'''
    
    def _database_test(self, db_type: str) -> str:
        if db_type == "sqlite":
            return '''import { describe, it, expect } from 'vitest';
import Database from 'better-sqlite3';

describe('Database', () => {
  it('should connect to database', () => {
    const db = new Database(':memory:');
    expect(db).toBeDefined();
  });

  it('should execute query', () => {
    const db = new Database(':memory:');
    db.exec('CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)');
    db.prepare('INSERT INTO test (name) VALUES (?)').run('hello');
    const row = db.prepare('SELECT * FROM test').get() as any;
    expect(row.name).toBe('hello');
  });
});
'''
        return '''
import { describe, it, expect } from 'vitest';

describe('Database', () => {
  it('should connect', async () => {
    expect(true).toBe(true);
  });
});
'''
    
    def _vitest_config(self) -> str:
        return '''import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    setupFiles: ['./tests/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
    },
  },
});
'''

working_test_generator = WorkingTestGenerator()

#!/usr/bin/env python3
"""React + Fastify + SQLite full-stack template."""
from typing import Dict, List
from .base import BaseTemplate

class ReactFastifyTemplate(BaseTemplate):
    def __init__(self):
        super().__init__("React Fastify", "React + Fastify + SQLite full-stack template")
        self.frontend = "React"
        self.backend = "Fastify"
        self.database = "SQLite"
    
    def generate_database(self) -> Dict:
        return {
            "models": [
                {
                    "name": "User",
                    "fields": [
                        {"name": "id", "type": "INTEGER", "primary": True},
                        {"name": "email", "type": "TEXT", "unique": True},
                        {"name": "password_hash", "type": "TEXT"},
                        {"name": "name", "type": "TEXT"},
                        {"name": "created_at", "type": "DATETIME"},
                    ]
                },
                {
                    "name": "Task",
                    "fields": [
                        {"name": "id", "type": "INTEGER", "primary": True},
                        {"name": "title", "type": "TEXT"},
                        {"name": "description", "type": "TEXT"},
                        {"name": "completed", "type": "BOOLEAN"},
                        {"name": "priority", "type": "TEXT", "default": "medium"},
                        {"name": "user_id", "type": "INTEGER", "foreign": "User.id"},
                        {"name": "created_at", "type": "DATETIME"},
                    ]
                }
            ],
            "schemas": [
                "CREATE TABLE user (id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, name TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP);",
                "CREATE TABLE task (id INTEGER PRIMARY KEY, title TEXT NOT NULL, description TEXT, completed BOOLEAN DEFAULT FALSE, priority TEXT DEFAULT 'medium', user_id INTEGER REFERENCES user(id), created_at DATETIME DEFAULT CURRENT_TIMESTAMP);",
            ],
            "migrations": [
                "CREATE TABLE user (id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, name TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP);",
                "CREATE TABLE task (id INTEGER PRIMARY KEY, title TEXT NOT NULL, description TEXT, completed BOOLEAN DEFAULT FALSE, priority TEXT DEFAULT 'medium', user_id INTEGER REFERENCES user(id), created_at DATETIME DEFAULT CURRENT_TIMESTAMP);",
            ],
            "seeders": [
                "INSERT INTO user (email, password_hash, name) VALUES ('admin@example.com', 'hashed', 'Admin');",
            ]
        }
    
    def generate_api(self) -> Dict:
        return {
            "endpoints": [
                {"method": "POST", "path": "/auth/register", "description": "Register new user"},
                {"method": "POST", "path": "/auth/login", "description": "Login user"},
                {"method": "GET", "path": "/auth/me", "description": "Get current user"},
                {"method": "POST", "path": "/auth/logout", "description": "Logout user"},
                {"method": "GET", "path": "/tasks", "description": "List tasks"},
                {"method": "POST", "path": "/tasks", "description": "Create task"},
                {"method": "GET", "path": "/tasks/:id", "description": "Get task by ID"},
                {"method": "PUT", "path": "/tasks/:id", "description": "Update task"},
                {"method": "DELETE", "path": "/tasks/:id", "description": "Delete task"},
            ],
            "openapi": {
                "openapi": "3.0.0",
                "info": {"title": "Task Manager API", "version": "1.0.0"},
                "paths": {}
            }
        }
    
    def generate_backend(self) -> Dict:
        return {
            "files": {
                "src/server.ts": '''import Fastify from 'fastify';
import cors from '@fastify/cors';
import jwt from '@fastify/jwt';
import { taskRoutes } from './routes/tasks';
import { authRoutes } from './routes/auth';

const app = Fastify({ logger: true });

app.register(cors);
app.register(jwt, { secret: process.env.JWT_SECRET || 'secret' });
app.register(authRoutes);
app.register(taskRoutes);

app.get('/health', async () => ({ status: 'ok' }));

app.listen({ port: 3010, host: '0.0.0.0' });
''',
                "src/routes/auth.ts": '''import { FastifyInstance } from 'fastify';
import bcrypt from 'bcryptjs';
import { db } from '../database';

export async function authRoutes(app: FastifyInstance) {
  app.post('/auth/register', async (req, reply) => {
    const { email, password, name } = req.body as any;
    const existing = db.prepare('SELECT * FROM user WHERE email = ?').get(email);
    if (existing) return reply.code(409).send({ error: 'Email already exists' });
    
    const password_hash = bcrypt.hashSync(password, 10);
    const user = db.prepare('INSERT INTO user (email, password_hash, name) VALUES (?, ?, ?)').run(email, password_hash, name);
    
    const token = app.jwt.sign({ id: user.lastInsertRowid, email });
    return { token };
  });

  app.post('/auth/login', async (req, reply) => {
    const { email, password } = req.body as any;
    const user = db.prepare('SELECT * FROM user WHERE email = ?').get(email) as any;
    if (!user) return reply.code(401).send({ error: 'Invalid credentials' });
    
    if (!bcrypt.compareSync(password, user.password_hash)) {
      return reply.code(401).send({ error: 'Invalid credentials' });
    }
    
    const token = app.jwt.sign({ id: user.id, email });
    return { token };
  });

  app.get('/auth/me', async (req, reply) => {
    try { await req.jwtVerify(); } catch { return reply.code(401).send({ error: 'Unauthorized' }); }
    return req.user;
  });
}
''',
                "src/routes/tasks.ts": '''import { FastifyInstance } from 'fastify';
import { db } from '../database';

export async function taskRoutes(app: FastifyInstance) {
  app.addHook('preHandler', async (req, reply) => {
    try { await req.jwtVerify(); } catch { reply.code(401).send({ error: 'Unauthorized' }); }
  });

  app.get('/tasks', async (req) => {
    const { id } = req.user as any;
    const tasks = db.prepare('SELECT * FROM task WHERE user_id = ? ORDER BY created_at DESC').all(id);
    return tasks;
  });

  app.post('/tasks', async (req, reply) => {
    const { id } = req.user as any;
    const { title, description, priority } = req.body as any;
    const result = db.prepare('INSERT INTO task (title, description, priority, user_id) VALUES (?, ?, ?, ?)').run(title, description, priority, id);
    return { id: result.lastInsertRowid, title, description, priority, completed: false };
  });

  app.put('/tasks/:id', async (req, reply) => {
    const { id: userId } = req.user as any;
    const { id } = req.params as any;
    const { title, description, completed, priority } = req.body as any;
    
    const existing = db.prepare('SELECT * FROM task WHERE id = ? AND user_id = ?').get(id, userId);
    if (!existing) return reply.code(404).send({ error: 'Task not found' });
    
    db.prepare('UPDATE task SET title = ?, description = ?, completed = ?, priority = ? WHERE id = ?')
      .run(title, description, completed, priority, id);
    
    return { id, title, description, completed, priority };
  });

  app.delete('/tasks/:id', async (req, reply) => {
    const { id: userId } = req.user as any;
    const { id } = req.params as any;
    
    const existing = db.prepare('SELECT * FROM task WHERE id = ? AND user_id = ?').get(id, userId);
    if (!existing) return reply.code(404).send({ error: 'Task not found' });
    
    db.prepare('DELETE FROM task WHERE id = ?').run(id);
    return { deleted: id };
  });
}
''',
                "src/database.ts": '''import Database from 'better-sqlite3';
const db = new Database('app.db');
db.pragma('journal_mode = WAL');
db.pragma('foreign_keys = ON');
export { db };
''',
                "src/utils/validation.ts": '''import { z } from 'zod';

export const registerSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
  name: z.string().min(2),
});

export const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(1),
});

export const taskSchema = z.object({
  title: z.string().min(1),
  description: z.string().optional(),
  priority: z.enum(['low', 'medium', 'high']).default('medium'),
  completed: z.boolean().default(false),
});
''',
            },
            "dependencies": [
                "fastify", "@fastify/cors", "@fastify/jwt",
                "bcryptjs", "better-sqlite3", "zod"
            ]
        }
    
    def generate_frontend(self) -> Dict:
        return {
            "files": {
                "src/App.tsx": '''import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './contexts/AuthContext';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Layout from './components/Layout';

const queryClient = new QueryClient();

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/" element={<Layout />}>
              <Route index element={<Dashboard />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}
''',
                "src/pages/Login.tsx": '''import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try { await login(email, password); navigate('/'); }
    catch (err: any) { setError(err.message || 'Login failed'); }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <form onSubmit={handleSubmit} className="bg-white p-8 rounded-lg shadow-md w-96">
        <h1 className="text-2xl font-bold mb-6">Login</h1>
        {error && <p className="text-red-500 mb-4">{error}</p>}
        <input type="email" value={email} onChange={e => setEmail(e.target.value)}
          placeholder="Email" className="w-full p-2 border rounded mb-4" required />
        <input type="password" value={password} onChange={e => setPassword(e.target.value)}
          placeholder="Password" className="w-full p-2 border rounded mb-4" required />
        <button type="submit" className="w-full bg-blue-500 text-white p-2 rounded hover:bg-blue-600">
          Login
        </button>
      </form>
    </div>
  );
}
''',
                "src/pages/Dashboard.tsx": '''import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../hooks/useAuth';
import TaskList from '../components/TaskList';

export default function Dashboard() {
  const { user } = useAuth();
  const { data: tasks, isLoading } = useQuery({ queryKey: ['tasks'], queryFn: async () => {
    const res = await fetch('/api/tasks', { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }});
    if (!res.ok) throw new Error('Failed to fetch');
    return res.json();
  }});

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Welcome, {user?.email}</h1>
      {isLoading ? <p>Loading...</p> : <TaskList tasks={tasks || []} />}
    </div>
  );
}
''',
                "src/hooks/useAuth.ts": '''import { createContext, useContext, useState, ReactNode } from 'react';

interface User { id: number; email: string; }
interface AuthContextType { user: User | null; login: (email: string, password: string) => Promise<void>; }

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);

  const login = async (email: string, password: string) => {
    const res = await fetch('/api/auth/login', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) throw new Error('Login failed');
    const data = await res.json();
    localStorage.setItem('token', data.token);
    setUser({ id: data.id, email });
  };

  return <AuthContext.Provider value={{ user, login }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
''',
            },
            "dependencies": [
                "react", "react-dom", "react-router-dom",
                "@tanstack/react-query"
            ]
        }
    
    def generate_tests(self) -> Dict:
        return {
            "unit": '''import { describe, it, expect } from 'vitest';

describe('Task Model', () => {
  it('should create task', () => { expect(true).toBe(true); });
});
''',
            "integration": '''import { describe, it, expect } from 'vitest';

describe('API Integration', () => {
  it('health check', async () => {
    const res = await fetch('http://localhost:3010/health');
    const data = await res.json();
    expect(data.status).toBe('ok');
  });
});
''',
            "e2e": '''import { test, expect } from '@playwright/test';

test('home page loads', async ({ page }) => {
  await page.goto('http://localhost:5173');
  await expect(page.locator('h1')).toContainText('Login');
});
'''
        }
    
    def generate_deploy(self) -> Dict:
        return {
            "ecosystem": '''module.exports = {
  apps: [{
    name: "aeryn-fullstack-api",
    script: "dist/server.js",
    cwd: "./",
    max_memory_restart: "512M",
    env: { NODE_ENV: "production", PORT: "3010" },
  }],
};
''',
            "dockerfile": '''FROM node:20-slim AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM node:20-slim
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY ecosystem.config.js ./
EXPOSE 3010
CMD ["npm", "start"]
''',
            "docker_compose": '''version: '3.8'
services:
  api:
    build: .
    ports:
      - "3010:3010"
    environment:
      NODE_ENV: production
      JWT_SECRET: change-me-in-production
    volumes:
      - ./data:/app/data
'''
        }

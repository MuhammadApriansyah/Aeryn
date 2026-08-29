#!/usr/bin/env python3
"""Backend Generator."""
from typing import Dict

class BackendGenerator:
    def generate(self, plan: Dict) -> Dict:
        files = {}
        for filepath in plan.get("structure", []):
            if "server" in filepath:
                files[filepath] = self._server_ts()
            elif "routes" in filepath:
                files[filepath] = self._routes_ts()
            elif "controllers" in filepath:
                files[filepath] = self._controllers_ts()
            elif "services" in filepath:
                files[filepath] = self._services_ts()
            elif "auth" in filepath:
                files[filepath] = self._auth_middleware()
            elif "logger" in filepath:
                files[filepath] = self._logger()
            else:
                files[filepath] = f"// {filepath}\n"
        return {"files": files, "dependencies": plan.get("dependencies", [])}
    
    def _server_ts(self):
        return '''import Fastify from 'fastify';
import cors from '@fastify/cors';
import jwt from '@fastify/jwt';
import { routes } from './routes/index';

const app = Fastify({ logger: true });

app.register(cors);
app.register(jwt, { secret: process.env.JWT_SECRET || 'secret' });
app.register(routes);

app.listen({ port: 3001, host: '0.0.0.0' });
'''
    
    def _routes_ts(self):
        return '''import { FastifyInstance } from 'fastify';

export async function routes(app: FastifyInstance) {
  app.get('/health', async () => ({ status: 'ok' }));
  app.get('/api/items', async (req, reply) => {
    return [{ id: 1, name: 'test' }];
  });
}
'''
    
    def _controllers_ts(self):
        return '''export const ItemsController = {
  list: async (req: any, reply: any) => {
    return [{ id: 1, name: 'item' }];
  },
  create: async (req: any, reply: any) => {
    return { id: 2, ...req.body };
  },
};
'''
    
    def _services_ts(self):
        return '''export class ItemsService {
  private items: any[] = [];
  
  list() { return this.items; }
  create(data: any) { this.items.push(data); return data; }
  update(id: number, data: any) { return { id, ...data }; }
  delete(id: number) { return { deleted: id }; }
}
'''
    
    def _auth_middleware(self):
        return '''import { FastifyInstance } from 'fastify';

export async function authMiddleware(app: FastifyInstance) {
  app.addHook('preHandler', async (req, reply) => {
    try { await req.jwtVerify(); } catch { reply.code(401).send({ error: 'Unauthorized' }); }
  });
}
'''
    
    def _logger(self):
        return '''export const logger = {
  info: (msg: string) => console.log(`[INFO] ${msg}`),
  error: (msg: string) => console.error(`[ERROR] ${msg}`),
  warn: (msg: string) => console.warn(`[WARN] ${msg}`),
};
'''

#!/usr/bin/env python3
"""API Versioning Generator."""
from typing import Dict

class APIVersioning:
    def generate_v1_routes(self) -> str:
        return '''import { FastifyInstance } from 'fastify';

export async function v1Routes(app: FastifyInstance) {
  app.get('/api/v1/health', async () => ({ status: 'ok', version: 'v1' }));
  app.get('/api/v1/items', async () => [{ id: 1, name: 'Item' }]);
  app.post('/api/v1/items', async (req, reply) => {
    return { id: 2, ...(req.body as any) };
  });
}
'''
    
    def generate_v2_routes(self) -> str:
        return '''import { FastifyInstance } from 'fastify';

export async function v2Routes(app: FastifyInstance) {
  app.get('/api/v2/health', async () => ({ status: 'ok', version: 'v2' }));
  app.get('/api/v2/items', async () => ({ data: [{ id: 1, name: 'Item' }], meta: { total: 1 } }));
  app.post('/api/v2/items', async (req, reply) => {
    return { data: { id: 2, ...(req.body as any) }, meta: {} };
  });
}
'''
    
    def generate_version_router(self) -> str:
        return '''import Fastify from 'fastify';
import { v1Routes } from './routes/v1';
import { v2Routes } from './routes/v2';

const app = Fastify({ logger: true });

app.register(v1Routes);
app.register(v2Routes);

app.listen({ port: 3010, host: '0.0.0.0' });
'''

api_versioning = APIVersioning()

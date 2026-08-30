import { FastifyInstance } from 'fastify';

export async function routes(app: FastifyInstance) {
  app.get('/api/items', async () => [{ id: 1, name: 'Item' }]);
  app.post('/api/items', async (req, reply) => {
    return { id: 2, ...(req.body as any) };
  });
}

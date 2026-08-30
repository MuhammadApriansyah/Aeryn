import Fastify from 'fastify';
import cors from '@fastify/cors';

const app = Fastify({ logger: true });
app.register(cors);

app.get('/health', async () => ({ status: 'ok' }));
app.get('/api/items', async () => [{ id: 1, name: 'Welcome to Aeryn!' }]);

app.listen({ port: 3010, host: '0.0.0.0' });

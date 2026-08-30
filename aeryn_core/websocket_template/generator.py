#!/usr/bin/env python3
"""WebSocket Template Generator."""
from typing import Dict

class WebSocketTemplate:
    def generate_websocket_server(self) -> str:
        return '''import Fastify from 'fastify';
import websocket from '@fastify/websocket';

const app = Fastify({ logger: true });
app.register(websocket);

app.register(async function (fastify) {
  fastify.get('/ws', { websocket: true }, (connection, req) => {
    connection.socket.on('message', (message) => {
      const data = JSON.parse(message.toString());
      connection.socket.send(JSON.stringify({ echo: data }));
    });
  });
});

app.listen({ port: 3010, host: '0.0.0.0' });
'''
    
    def generate_websocket_client(self) -> str:
        return '''// WebSocket Client
const ws = new WebSocket('ws://localhost:3010/ws');

ws.onopen = () => {
  console.log('Connected to server');
  ws.send(JSON.stringify({ message: 'Hello!' }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Disconnected');
};
'''
    
    def generate_sse_server(self) -> str:
        return '''import Fastify from 'fastify';

const app = Fastify({ logger: true });

app.get('/events', (req, reply) => {
  reply.raw.writeHead(200, {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
  });
  
  // Send event every 5 seconds
  const interval = setInterval(() => {
    reply.raw.write(`data: ${JSON.stringify({ time: new Date().toISOString() })}\n\n`);
  }, 5000);
  
  req.raw.on('close', () => clearInterval(interval));
});

app.listen({ port: 3010, host: '0.0.0.0' });
'''
    
    def get_dependencies(self):
        return ["@fastify/websocket"]

websocket_template = WebSocketTemplate()

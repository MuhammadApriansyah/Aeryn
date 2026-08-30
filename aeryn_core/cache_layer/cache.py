#!/usr/bin/env python3
"""Cache Layer — Redis caching template."""
from typing import Dict

class CacheLayer:
    def generate_redis_config(self) -> Dict:
        return {
            "config/redis.js": """import Redis from 'ioredis';
const redis = new Redis({ host: process.env.REDIS_HOST || 'localhost', port: parseInt(process.env.REDIS_PORT || '6379') });
export { redis };
""",
            "middleware/cache.js": """import { redis } from '../config/redis.js';
export function cacheMiddleware(duration = 300) {
  return async (req, reply) => {
    const key = `cache:${req.url}`;
    const cached = await redis.get(key);
    if (cached) { reply.header('X-Cache', 'HIT'); return JSON.parse(cached); }
    reply.header('X-Cache', 'MISS');
  };
}
""",
        }
    
    def get_dependencies(self):
        return ["ioredis"]

cache_layer = CacheLayer()

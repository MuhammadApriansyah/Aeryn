#!/usr/bin/env python3
"""Vue + Fastify + SQLite full-stack template."""
from typing import Dict
from .base import BaseTemplate

class VueFastifyTemplate(BaseTemplate):
    def __init__(self):
        super().__init__("Vue Fastify", "Vue + Fastify + SQLite full-stack template")
        self.frontend = "Vue"
        self.backend = "Fastify"
        self.database = "SQLite"
    
    def generate_frontend(self) -> Dict:
        return {
            "files": {
                "src/App.vue": '''<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { RouterView } from 'vue-router';
</script>
''',
                "src/main.ts": '''import { createApp } from 'vue';
import { createRouter, createWebHistory } from 'vue-router';
import App from './App.vue';
import Home from './views/Home.vue';
import Login from './views/Login.vue';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: Home },
    { path: '/login', component: Login },
  ],
});

createApp(App).use(router).mount('#app');
''',
                "src/views/Home.vue": '''<template>
  <div>
    <h1>Welcome to Aeryn</h1>
    <p>Vue + Fastify + SQLite</p>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';

const message = ref('Loading...');
onMounted(async () => {
  message.value = 'Ready!';
});
</script>
''',
            },
            "dependencies": ["vue", "vue-router", "@vue/compat"]
        }
    
    def generate_backend(self) -> Dict:
        return {
            "files": {
                "src/server.ts": '''import Fastify from 'fastify';
import cors from '@fastify/cors';

const app = Fastify({ logger: true });
app.register(cors);

app.get('/health', async () => ({ status: 'ok' }));
app.get('/api/items', async () => [{ id: 1, name: 'test' }]);

app.listen({ port: 3010, host: '0.0.0.0' });
''',
            },
            "dependencies": ["fastify", "@fastify/cors"]
        }

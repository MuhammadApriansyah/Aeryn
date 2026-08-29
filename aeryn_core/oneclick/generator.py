#!/usr/bin/env python3
"""One-Click Generator — Minimal questions, instant project."""
import os
import shutil
import tempfile
from typing import Dict, Optional

class OneClickGenerator:
    """Generate project with minimal user input."""
    
    def __init__(self):
        self._default_tech_stack = {
            "frontend": "React",
            "backend": "Fastify",
            "database": "SQLite",
            "auth": True,
        }
    
    def generate(self, name: str, template: str = "fullstack") -> Dict:
        """Generate project with one click."""
        project_dir = os.path.join(os.getcwd(), name)
        
        if os.path.exists(project_dir):
            return {"error": f"Folder '{name}' sudah ada"}
        
        os.makedirs(project_dir)
        
        # Generate based on template
        if template == "fullstack":
            return self._generate_fullstack(name, project_dir)
        elif template == "api":
            return self._generate_api(name, project_dir)
        elif template == "bot":
            return self._generate_bot(name, project_dir)
        else:
            return self._generate_fullstack(name, project_dir)
    
    def _generate_fullstack(self, name: str, project_dir: str) -> Dict:
        """Generate fullstack project."""
        files = {}
        
        # Backend
        backend_dir = os.path.join(project_dir, "api")
        os.makedirs(backend_dir, exist_ok=True)
        
        files["api/server.ts"] = self._backend_server()
        files["api/routes/index.ts"] = self._backend_routes()
        files["api/database.ts"] = self._backend_database()
        files["api/package.json"] = self._backend_package_json(name)
        
        # Frontend
        frontend_dir = os.path.join(project_dir, "web")
        os.makedirs(frontend_dir, exist_ok=True)
        
        files["web/src/App.tsx"] = self._frontend_app()
        files["web/src/main.tsx"] = self._frontend_main()
        files["web/package.json"] = self._frontend_package_json(name)
        
        # Root files
        files["README.md"] = self._readme(name)
        files[".gitignore"] = self._gitignore()
        
        # Write all files
        self._write_project_files(project_dir, files)
        
        return {
            "name": name,
            "path": project_dir,
            "type": "fullstack",
            "files_created": len(files),
        }
    
    def _generate_api(self, name: str, project_dir: str) -> Dict:
        """Generate API-only project."""
        files = {}
        
        files["server.ts"] = self._backend_server()
        files["routes/index.ts"] = self._backend_routes()
        files["database.ts"] = self._backend_database()
        files["package.json"] = self._backend_package_json(name)
        files["README.md"] = self._readme(name)
        files[".gitignore"] = self._gitignore()
        
        self._write_project_files(project_dir, files)
        
        return {
            "name": name,
            "path": project_dir,
            "type": "api",
            "files_created": len(files),
        }
    
    def _generate_bot(self, name: str, project_dir: str) -> Dict:
        """Generate bot project."""
        files = {}
        
        files["bot.ts"] = self._bot_code()
        files["package.json"] = self._bot_package_json(name)
        files["README.md"] = self._readme(name)
        files[".gitignore"] = self._gitignore()
        
        self._write_project_files(project_dir, files)
        
        return {
            "name": name,
            "path": project_dir,
            "type": "bot",
            "files_created": len(files),
        }
    
    def _write_project_files(self, project_dir: str, files: Dict):
        """Write files to project directory."""
        for filepath, content in files.items():
            full_path = os.path.join(project_dir, filepath)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w") as f:
                f.write(content)
    
    def _backend_server(self):
        return '''import Fastify from 'fastify';
import cors from '@fastify/cors';

const app = Fastify({ logger: true });
app.register(cors);

app.get('/health', async () => ({ status: 'ok' }));
app.get('/api/items', async () => [{ id: 1, name: 'Welcome to Aeryn!' }]);

app.listen({ port: 3010, host: '0.0.0.0' });
'''
    
    def _backend_routes(self):
        return '''import { FastifyInstance } from 'fastify';

export async function routes(app: FastifyInstance) {
  app.get('/api/items', async () => [{ id: 1, name: 'Item' }]);
  app.post('/api/items', async (req, reply) => {
    return { id: 2, ...(req.body as any) };
  });
}
'''
    
    def _backend_database(self):
        return '''import Database from 'better-sqlite3';
const db = new Database('app.db');
db.pragma('journal_mode = WAL');
db.pragma('foreign_keys = ON');
export { db };
'''
    
    def _backend_package_json(self, name):
        return f'''{{
  "name": "{name}-api",
  "version": "1.0.0",
  "scripts": {{
    "dev": "tsx watch server.ts",
    "build": "tsc",
    "start": "node dist/server.js"
  }},
  "dependencies": {{
    "fastify": "^4.0.0",
    "@fastify/cors": "^9.0.0",
    "better-sqlite3": "^9.0.0"
  }},
  "devDependencies": {{
    "tsx": "^4.0.0",
    "typescript": "^5.0.0"
  }}
}}
'''
    
    def _frontend_app(self):
        return '''export default function App() {
  return (
    <div style={{ fontFamily: 'system-ui', padding: '2rem' }}>
      <h1>🚀 Welcome to Aeryn</h1>
      <p>Your full-stack app is ready!</p>
    </div>
  );
}
'''
    
    def _frontend_main(self):
        return '''import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
'''
    
    def _frontend_package_json(self, name):
        return f'''{{
  "name": "{name}-web",
  "version": "1.0.0",
  "scripts": {{
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  }},
  "dependencies": {{
    "react": "^18.0.0",
    "react-dom": "^18.0.0"
  }},
  "devDependencies": {{
    "@vitejs/plugin-react": "^4.0.0",
    "vite": "^5.0.0"
  }}
}}
'''
    
    def _bot_code(self):
        return '''import { Client, GatewayIntentBits } from 'discord.js';

const client = new Client({ intents: [GatewayIntentBits.Guilds] });

client.on('ready', () => {
  console.log(`Logged in as ${client.user?.tag}`);
});

client.on('interactionCreate', async (interaction) => {
  if (!interaction.isChatInputCommand()) return;
  if (interaction.commandName === 'ping') {
    await interaction.reply('Pong!');
  }
});

client.login(process.env.DISCORD_TOKEN);
'''
    
    def _bot_package_json(self, name):
        return f'''{{
  "name": "{name}-bot",
  "version": "1.0.0",
  "scripts": {{
    "dev": "tsx watch bot.ts",
    "start": "node dist/bot.js"
  }},
  "dependencies": {{
    "discord.js": "^14.0.0"
  }},
  "devDependencies": {{
    "tsx": "^4.0.0",
    "typescript": "^5.0.0"
  }}
}}
'''
    
    def _readme(self, name):
        return f'''# {name}

Generated by Aeryn 🚀

## Getting Started

### Backend
```bash
cd api
npm install
npm run dev
```

### Frontend
```bash
cd web
npm install
npm run dev
```

## API Endpoints

- `GET /health` — Health check
- `GET /api/items` — List items
- `POST /api/items` — Create item
'''
    
    def _gitignore(self):
        return '''node_modules/
dist/
.env
*.db
.DS_Store
'''

oneclick_generator = OneClickGenerator()

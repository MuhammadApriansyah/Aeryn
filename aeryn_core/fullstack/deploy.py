#!/usr/bin/env python3
"""Deploy Manager."""
from typing import Dict

class DeployManager:
    def generate(self, plan: Dict) -> Dict:
        return {
            "ecosystem": self._ecosystem_config(plan),
            "dockerfile": self._dockerfile(plan),
            "docker_compose": self._docker_compose(plan),
            "scripts": self._deploy_scripts(plan),
        }
    
    def _ecosystem_config(self, plan: Dict) -> str:
        return '''module.exports = {
  apps: [{
    name: "aeryn-api",
    script: "src/server.ts",
    interpreter: "./node_modules/.bin/tsx",
    cwd: "./",
    max_memory_restart: "512M",
    env: {
      NODE_ENV: "production",
      PORT: "3010",
    },
  }],
};
'''
    
    def _dockerfile(self, plan: Dict) -> str:
        return '''FROM node:20-slim

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

RUN npm run build

EXPOSE 3010

CMD ["npm", "start"]
'''
    
    def _docker_compose(self, plan: Dict) -> str:
        return '''version: '3.8'

services:
  api:
    build: .
    ports:
      - "3010:3010"
    environment:
      NODE_ENV: production
      DATABASE_URL: postgresql://user:pass@db:5432/app
    depends_on:
      - db

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: app
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
'''
    
    def _deploy_scripts(self, plan: Dict) -> Dict:
        return {
            "deploy.sh": '#!/bin/bash\necho "Deploying..."\ndocker-compose up -d --build',
            "rollback.sh": '#!/bin/bash\necho "Rolling back..."\ndocker-compose down',
        }

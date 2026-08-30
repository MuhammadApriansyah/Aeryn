#!/usr/bin/env python3
"""CI/CD Template Generator."""
from typing import Dict

class CICDGenerator:
    def generate_github_actions(self, project_info: Dict) -> Dict:
        return {
            ".github/workflows/ci.yml": self._github_actions_ci(project_info),
            ".github/workflows/deploy.yml": self._github_actions_deploy(project_info),
        }
    
    def _github_actions_ci(self, info: Dict) -> str:
        return f'''name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '20'
        cache: 'npm'
    
    - name: Install dependencies
      run: npm ci
    
    - name: Run tests
      run: npm test
    
    - name: Build
      run: npm run build

  lint:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-node@v4
      with:
        node-version: '20'
    - run: npm ci
    - run: npm run lint
'''
    
    def _github_actions_deploy(self, info: Dict) -> str:
        return f'''name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    needs: test
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '20'
    
    - name: Install and build
      run: |
        npm ci
        npm run build
    
    - name: Deploy to production
      run: echo "Add your deploy command here"
      env:
        DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}
'''

cicd_generator = CICDGenerator()

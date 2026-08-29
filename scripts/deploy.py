#!/usr/bin/env python3
"""
V41.0 — Aeryn Deploy.
Deploy Aeryn ke production.
"""
import os
import subprocess
import sys

os.chdir('/home/sen/aeryn-core-agent')

def deploy():
    """Deploy Aeryn."""
    print("🚀 Deploying Aeryn...")
    
    # 1. Run tests
    print("  Running tests...")
    result = subprocess.run(['./venv-proot/bin/python', '-m', 'pytest', 'tests/', '-q'], capture_output=True)
    if result.returncode != 0:
        print("  ❌ Tests failed!")
        print(result.stdout.decode())
        return False
    print("  ✅ Tests pass")
    
    # 2. Stop existing process
    print("  Stopping existing process...")
    subprocess.run(['pm2', 'stop', 'aeryn-api'], capture_output=True)
    
    # 3. Start with PM2
    print("  Starting with PM2...")
    result = subprocess.run(['pm2', 'start', 'ecosystem.config.cjs'], capture_output=True)
    if result.returncode != 0:
        print("  ❌ PM2 start failed!")
        print(result.stderr.decode())
        return False
    print("  ✅ PM2 started")
    
    # 4. Health check
    print("  Running health check...")
    import urllib.request
    try:
        req = urllib.request.Request('http://127.0.0.1:3010/health')
        resp = urllib.request.urlopen(req, timeout=10)
        data = resp.read().decode()
        print(f"  ✅ Health check OK: {data}")
    except Exception as e:
        print(f"  ❌ Health check failed: {e}")
        return False
    
    print("✅ Deploy complete!")
    return True

if __name__ == '__main__':
    success = deploy()
    sys.exit(0 if success else 1)

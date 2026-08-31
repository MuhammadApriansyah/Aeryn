#!/usr/bin/env python3
"""V61.1 — Aeryn One-Click Launcher (D4: Ease of Access).

Detects environment, configures services, and starts Aeryn.
Usage: python -m aeryn_core.launcher [start|stop|status|env]
"""
import os
import sys
import json
import time
import shutil
import subprocess
import signal
from pathlib import Path


def detect_environment():
    """Detect runtime environment."""
    env = os.environ.get("AERYN_ENV", "")
    if env:
        return env
    # Check proot
    try:
        with open("/proc/1/comm", "r") as f:
            comm = f.read().strip().lower()
        if "proot" in comm or "termux" in comm:
            return "proot"
    except:
        pass
    if os.path.exists("/var/run/secrets/kubernetes.io/serviceaccount"):
        return "k8s"
    if os.path.exists("/.dockerenv"):
        return "docker"
    if os.path.exists("/etc/systemd/system"):
        return "vps"
    return "unknown"


def get_config(env):
    """Get configuration for the detected environment."""
    base_dir = Path(os.environ.get("AERYN_BASE_DIR", Path.home() / "aeryn-core-agent"))
    configs = {
        "proot": {
            "host": "127.0.0.1",
            "port": 3010,
            "dashboard_port": 3020,
            "supervisor": "pm2",
            "db": "sqlite",
            "workers": 2,
        },
        "vps": {
            "host": "127.0.0.1",
            "port": 3010,
            "dashboard_port": 3020,
            "supervisor": "pm2",
            "db": os.environ.get("DATABASE_URL", "sqlite"),
            "workers": 4,
        },
        "k8s": {
            "host": "0.0.0.0",
            "port": int(os.environ.get("AERYN_PORT", 3010)),
            "dashboard_port": int(os.environ.get("AERYN_DASHBOARD_PORT", 3020)),
            "supervisor": "none",
            "db": os.environ.get("DATABASE_URL", "postgres"),
            "workers": 1,
        },
        "docker": {
            "host": "0.0.0.0",
            "port": int(os.environ.get("AERYN_PORT", 3010)),
            "dashboard_port": int(os.environ.get("AERYN_DASHBOARD_PORT", 3020)),
            "supervisor": "none",
            "db": os.environ.get("DATABASE_URL", "postgres"),
            "workers": 1,
        },
    }
    config = configs.get(env, configs["proot"])
    config["env"] = env
    config["base_dir"] = str(base_dir)
    return config


def generate_ecosystem(config, output_path):
    """Generate ecosystem.config.cjs from template."""
    script_dir = Path(__file__).parent.parent.parent
    template = script_dir / "ecosystem.config.cjs"
    
    if template.exists():
        return str(template)
    
    # Generate if not exists
    ecosystem = f"""
module.exports = {{
  apps: [
    {{
      name: "aeryn-api",
      script: "apps/api/routers/main.py",
      interpreter: "./venv-proot/bin/python",
      cwd: "{config['base_dir']}",
      watch: false,
      max_memory_restart: "512M",
      env: {{
        NODE_ENV: "production",
        AERYN_MODE: "standalone",
        AERYN_PORT: "{config['port']}",
        AERYN_HOST: "{config['host']}",
        AERYN_ENV: "{config['env']}",
        PYTHONUNBUFFERED: "1",
        TZ: "{os.environ.get('TZ', 'UTC')}",
      }},
      error_file: "logs/aeryn-api-error.log",
      out_file: "logs/aeryn-api-out.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss",
      merge_logs: true,
      instances: 1,
      exec_mode: "fork",
      autorestart: true,
      max_restarts: 20,
      min_uptime: "10s",
      restart_delay: 4000,
      wait_ready: true,
      kill_timeout: 5000,
      listen_timeout: 8000,
    }},
    {{
      name: "aeryn-dashboard",
      script: "aeryn_core/dashboard/run_server.py",
      interpreter: "./venv-proot/bin/python",
      cwd: "{config['base_dir']}",
      watch: false,
      max_memory_restart: "256M",
      env: {{
        PYTHONPATH: "{config['base_dir']}",
        AERYN_DASHBOARD_PORT: "{config['dashboard_port']}",
        AERYN_DASHBOARD_HOST: "127.0.0.1",
        PYTHONUNBUFFERED: "1",
        TZ: "{os.environ.get('TZ', 'UTC')}",
      }},
      error_file: "logs/aeryn-dashboard-error.log",
      out_file: "logs/aeryn-dashboard-out.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss",
      merge_logs: true,
      instances: 1,
      exec_mode: "fork",
      autorestart: true,
      max_restarts: 10,
      min_uptime: "10s",
      restart_delay: 2000,
    }},
  ],
}};
"""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(ecosystem)
    return str(output_path)


def cmd_start(config):
    """Start Aeryn services."""
    print(f"🚀 Starting Aeryn (env: {config['env']})...")
    
    # Generate ecosystem config
    ecosystem_path = Path(config["base_dir"]) / "ecosystem.config.cjs"
    if not ecosystem_path.exists():
        generate_ecosystem(config, ecosystem_path)
        print(f"  Generated {ecosystem_path}")
    
    # Check pm2
    if shutil.which("pm2"):
        subprocess.run(["pm2", "start", str(ecosystem_path)], cwd=config["base_dir"])
        print("  ✅ Started via PM2")
    else:
        print("  ⚠️ PM2 not found. Running backend directly...")
        # Start backend directly
        backend = Path(config["base_dir"]) / "apps/api/routers/main.py"
        if backend.exists():
            subprocess.Popen(
                [sys.executable, str(backend)],
                cwd=config["base_dir"],
                stdout=open("logs/aeryn-api-out.log", "a"),
                stderr=open("logs/aeryn-api-error.log", "a"),
            )
            print(f"  ✅ Backend started on port {config['port']}")
    
    # Show status
    cmd_status(config)


def cmd_stop(config):
    """Stop Aeryn services."""
    print("🛑 Stopping Aeryn...")
    if shutil.which("pm2"):
        subprocess.run(["pm2", "stop", "aeryn-api", "aeryn-dashboard"])
        print("  ✅ Stopped via PM2")
    else:
        # Kill by port
        subprocess.run(["pkill", "-f", "routers/main.py"])
        subprocess.run(["pkill", "-f", "run_server.py"])
        print("  ✅ Stopped processes")


def cmd_status(config):
    """Show Aeryn status."""
    print(f"📊 Aeryn Status (env: {config['env']})")
    print(f"  Base: {config['base_dir']}")
    print(f"  API: http://{config['host']}:{config['port']}")
    print(f"  Dashboard: http://127.0.0.1:{config['dashboard_port']}")
    print(f"  DB: {config['db']}")
    print(f"  Workers: {config['workers']}")
    
    if shutil.which("pm2"):
        result = subprocess.run(["pm2", "list"], capture_output=True, text=True)
        if result.stdout:
            for line in result.stdout.splitlines():
                if "aeryn" in line:
                    print(f"  {line.strip()}")


def cmd_env(config):
    """Show detected environment."""
    print(f"Environment: {config['env']}")
    print(f"Configuration:")
    for k, v in config.items():
        print(f"  {k}: {v}")


def main():
    if len(sys.argv) < 2:
        print("Usage: aeryn [start|stop|status|env]")
        sys.exit(1)
    
    command = sys.argv[1]
    env = detect_environment()
    config = get_config(env)
    
    commands = {
        "start": cmd_start,
        "stop": cmd_stop,
        "status": cmd_status,
        "env": cmd_env,
    }
    
    func = commands.get(command)
    if func:
        func(config)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()

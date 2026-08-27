module.exports = {
  apps: [
    {
      name: "aeryn-api",
      script: "apps/api/aeryn_api.py",
      interpreter: "./venv-proot/bin/python",
      cwd: "/home/sen/aeryn-core-agent",
      args: "--host 127.0.0.1 --port 3010",
      watch: false,
      max_memory_restart: "512M",
      env: {
        NODE_ENV: "production",
        AERYN_PORT: "3010",
        AERYN_HOST: "127.0.0.1",
      },
      error_file: "logs/aeryn-api-error.log",
      out_file: "logs/aeryn-api-out.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss",
      merge_logs: true,
      instances: 1,
      exec_mode: "fork",
      autorestart: true,
      max_restarts: 10,
      min_uptime: "10s",
    },
  ],
};

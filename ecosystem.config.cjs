module.exports = {
  apps: [
    {
      name: 'aeryn-api',
      cwd: '/data/data/com.termux/files/home/aeryn-core-agent',
      script: '/data/data/com.termux/files/home/aeryn-venv/bin/python',
      args: '-m apps.api.routers.main',
      env: {
        NEON_DATABASE_URL: 'postgresql://sen@127.0.0.1:5432/aeryn',
        AERYN_HOST: '127.0.0.1',
        AERYN_PORT: '3010',
        HOME: '/data/data/com.termux/files/home',
        PREFIX: '/data/data/com.termux/files/usr',
      },
      max_memory_restart: '600M',
      autorestart: true,
    },
  ],
};

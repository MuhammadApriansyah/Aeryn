module.exports = {
  apps: [{
    name: 'aeryn-core',
    script: 'scripts/aeryn_daemon.py',
    interpreter: './venv-proot/bin/python',
    cwd: '/home/sen/aeryn-core-agent',
    env: {
      NODE_ENV: 'production'
    }
  }]
};

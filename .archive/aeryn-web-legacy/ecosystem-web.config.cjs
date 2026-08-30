module.exports = {
  apps: [
    {
      name: "aeryn-web",
      script: "/home/sen/aeryn-core-agent/aeryn-web/start.sh",
      env: {
        "NODE_ENV": "production"
      },
      autorestart: false,
      watch: false
    }
  ]
};

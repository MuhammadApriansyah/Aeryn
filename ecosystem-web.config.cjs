module.exports = {
  apps: [
    {
      name: "aeryn-web",
      script: "/home/sen/aeryn-core-agent/aeryn-web/start.sh",
      env: { "NODE_ENV": "development" },
      error_file: "./logs/aeryn-web-error.log",
      out_file: "./logs/aeryn-web-out.log",
      autorestart: false,
      watch: false
    }
  ]
};

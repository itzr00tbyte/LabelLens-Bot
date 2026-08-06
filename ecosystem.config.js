module.exports = {
  apps: [
    {
      name: "labellens-bot",
      script: "-m",
      args: "app.main",
      interpreter: "./.venv/bin/python",
      cwd: "./",
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: "1G",
      restart_delay: 3000,
      env: {
        PYTHONUNBUFFERED: "1",
        OMP_NUM_THREADS: "2",
        ENVIRONMENT: "production"
      },
      error_file: "./logs/pm2-error.log",
      out_file: "./logs/pm2-out.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss Z",
      merge_logs: true
    }
  ]
};

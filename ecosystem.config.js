const fs = require('fs');
const path = require('path');

// Automatically use .venv python if present, otherwise fallback to global system python3
const venvPython = path.join(__dirname, '.venv', 'bin', 'python');
const interpreter = fs.existsSync(venvPython) ? venvPython : 'python3';

module.exports = {
  apps: [
    {
      name: "labellens-bot",
      script: "app/main.py",
      interpreter: interpreter,
      cwd: "./",
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: "1G",
      restart_delay: 3000,
      env: {
        PYTHONPATH: ".",
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

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

      // Restart loop protection: stop restarting after 10 crashes in < 5s
      max_restarts: 10,
      min_uptime: 5000,       // Must stay up 5s to count as a stable start
      restart_delay: 3000,    // Wait 3s between restarts

      // Memory guard: restart if process exceeds 1GB
      max_memory_restart: "1G",

      // Graceful shutdown: give bot 10s to finish in-flight requests on SIGTERM
      kill_timeout: 10000,
      wait_ready: false,

      env: {
        PYTHONPATH: ".",
        PYTHONUNBUFFERED: "1",
        OMP_NUM_THREADS: "2",
        TESSERACT_CMD: "/usr/bin/tesseract",
        ENVIRONMENT: "production",
        LOG_LEVEL: "INFO",
      },

      // Logs go to logs/ directory (consistent with logging_config.py)
      error_file: "./logs/pm2-error.log",
      out_file: "./logs/pm2-out.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss Z",
      merge_logs: true,
    }
  ]
};

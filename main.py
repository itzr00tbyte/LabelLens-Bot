#!/usr/bin/env python3
"""
Root entry point for LabelLens Telegram Bot.
Allows running directly with: python main.py
"""
import asyncio
import os
import subprocess
import sys

# Ensure root project directory is first in sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ["PYTHONPATH"] = PROJECT_ROOT
os.environ["PYTHONUNBUFFERED"] = "1"


def run_migrations() -> None:
    """Applies Alembic database migrations before bot startup."""
    try:
        print("[1/2] Checking & applying database migrations...")
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print("[✓] Database migrations up-to-date.")
        else:
            print(f"[!] Migration warning: {result.stderr.strip() or result.stdout.strip()}")
    except Exception as exc:
        print(f"[!] Migration check skipped: {exc}")


def cleanup_stale_instances() -> None:
    """Terminates any stale background bot process to prevent Telegram Conflict error."""
    try:
        curr_pid = str(os.getpid())
        # Run pkill only for other python main.py or python -m app.main processes
        cmd = f"pgrep -f 'app.main|main.py' | grep -v {curr_pid} | xargs kill -9 2>/dev/null || true"
        subprocess.run(cmd, shell=True)
    except Exception:
        pass


if __name__ == "__main__":
    cleanup_stale_instances()
    run_migrations()
    print("[2/2] Launching LabelLens Telegram Bot...\n")

    from app.main import main
    asyncio.run(main())

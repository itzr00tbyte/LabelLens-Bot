import logging
import logging.handlers
import sys
from colorama import Fore, Style, init

from app.config import settings

# Initialize colorama
init(autoreset=True)


class ColorizedFormatter(logging.Formatter):
    """Console formatter with per-level ANSI colours and optional traceback."""

    LEVEL_COLORS = {
        logging.DEBUG: Fore.CYAN + Style.DIM,
        logging.INFO: Fore.GREEN + Style.BRIGHT,
        logging.WARNING: Fore.YELLOW + Style.BRIGHT,
        logging.ERROR: Fore.RED + Style.BRIGHT,
        logging.CRITICAL: Fore.MAGENTA + Style.BRIGHT,
    }

    def format(self, record: logging.LogRecord) -> str:
        color = self.LEVEL_COLORS.get(record.levelno, Fore.WHITE)
        timestamp = (
            f"{Fore.BLACK}{Style.BRIGHT}"
            f"[{self.formatTime(record, self.datefmt)}]"
            f"{Style.RESET_ALL}"
        )
        level_str = f"{color}[{record.levelname:<8}]{Style.RESET_ALL}"
        name_str = f"{Fore.BLUE}[{record.name}]{Style.RESET_ALL}"
        msg = (
            f"{Style.BRIGHT}{record.getMessage()}{Style.RESET_ALL}"
            if record.levelno >= logging.WARNING
            else record.getMessage()
        )
        line = f"{timestamp} {level_str} {name_str} - {msg}"

        # Append formatted exception traceback when present
        if record.exc_info:
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            line = f"{line}\n{Fore.RED}{record.exc_text}{Style.RESET_ALL}"
        if record.stack_info:
            line = f"{line}\n{self.formatStack(record.stack_info)}"
        return line


class PlainFormatter(logging.Formatter):
    """Plain (no ANSI) formatter for log file output."""

    def format(self, record: logging.LogRecord) -> str:
        timestamp = self.formatTime(record, self.datefmt)
        line = f"[{timestamp}] [{record.levelname:<8}] [{record.name}] - {record.getMessage()}"
        if record.exc_info:
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            line = f"{line}\n{record.exc_text}"
        if record.stack_info:
            line = f"{line}\n{self.formatStack(record.stack_info)}"
        return line


def setup_logging() -> None:
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers to prevent duplicates
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)

    # ── Console handler (colourized) ────────────────────────────────────────
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColorizedFormatter(datefmt="%Y-%m-%d %H:%M:%S"))
    root_logger.addHandler(console_handler)

    # ── Rotating file handler (plain text, always at DEBUG level) ───────────
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            "bot.log",
            maxBytes=5 * 1024 * 1024,  # 5 MB per file
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(PlainFormatter(datefmt="%Y-%m-%d %H:%M:%S"))
        root_logger.addHandler(file_handler)
    except OSError as exc:
        root_logger.warning("Could not open log file for writing: %s", exc)

    # ── Suppress noisy third-party loggers ──────────────────────────────────
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.INFO)
    logging.getLogger("telegram.ext.ConversationHandler").setLevel(logging.DEBUG)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)

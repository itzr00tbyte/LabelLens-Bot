import logging
import sys
from colorama import Fore, Style, init

from app.config import settings

# Initialize colorama
init(autoreset=True)


class ColorizedFormatter(logging.Formatter):
    LEVEL_COLORS = {
        logging.DEBUG: Fore.CYAN + Style.DIM,
        logging.INFO: Fore.GREEN + Style.BRIGHT,
        logging.WARNING: Fore.YELLOW + Style.BRIGHT,
        logging.ERROR: Fore.RED + Style.BRIGHT,
        logging.CRITICAL: Fore.MAGENTA + Style.BRIGHT,
    }

    def format(self, record: logging.LogRecord) -> str:
        color = self.LEVEL_COLORS.get(record.levelno, Fore.WHITE)
        timestamp = f"{Fore.BLACK}{Style.BRIGHT}[{self.formatTime(record, self.datefmt)}]{Style.RESET_ALL}"
        level_str = f"{color}[{record.levelname}]{Style.RESET_ALL}"
        name_str = f"{Fore.BLUE}[{record.name}]{Style.RESET_ALL}"
        msg = f"{Style.BRIGHT}{record.getMessage()}{Style.RESET_ALL}" if record.levelno >= logging.WARNING else record.getMessage()
        return f"{timestamp} {level_str} {name_str} - {msg}"


def setup_logging() -> None:
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    formatter = ColorizedFormatter(datefmt="%Y-%m-%d %H:%M:%S")

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers to prevent duplicates
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)

    root_logger.addHandler(handler)

    # Lower third party verbosity
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

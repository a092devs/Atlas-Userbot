import logging
from pathlib import Path

LOG_FILE_PATH = Path("log.txt")

# -------------------------------------------------
# Logger setup
# -------------------------------------------------
_logger = logging.getLogger("atlas")
_logger.setLevel(logging.INFO)

_formatter = logging.Formatter(
    "[%(asctime)s] [%(levelname)s] %(message)s",
    "%Y-%m-%d %H:%M:%S",
)

# Console handler
_console = logging.StreamHandler()
_console.setFormatter(_formatter)

# File handler (THIS is what was missing)
_file = logging.FileHandler(LOG_FILE_PATH, encoding="utf-8")
_file.setFormatter(_formatter)

_logger.addHandler(_console)
_logger.addHandler(_file)


# -------------------------------------------------
# Public helpers
# -------------------------------------------------
def clear_logs():
    LOG_FILE_PATH.write_text("", encoding="utf-8")


def set_log_level(level: str):
    _logger.setLevel(getattr(logging, level))


def get_log_level() -> str:
    return logging.getLevelName(_logger.level)


# Expose logger
log = _logger
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler

LOG_FILE_PATH = Path("log.txt")

# -------------------------------------------------
# Logger setup
# -------------------------------------------------
log = logging.getLogger("atlas")
log.setLevel(logging.DEBUG)

_formatter = logging.Formatter(
    fmt="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# -------------------------------------------------
# File handler (rotating)
# -------------------------------------------------
_file_handler = RotatingFileHandler(
    LOG_FILE_PATH,
    maxBytes=50 * 1024 * 1024,  # 5 MB
    backupCount=3,
    encoding="utf-8",
)
_file_handler.setFormatter(_formatter)
_file_handler.setLevel(logging.DEBUG)

# -------------------------------------------------
# Console handler (optional, useful for dev)
# -------------------------------------------------
_console_handler = logging.StreamHandler()
_console_handler.setFormatter(_formatter)
_console_handler.setLevel(logging.INFO)

# -------------------------------------------------
# Attach handlers (avoid duplicates)
# -------------------------------------------------
if not log.handlers:
    log.addHandler(_file_handler)
    log.addHandler(_console_handler)

log.propagate = False

def clear_logs():
    try:
        if LOG_FILE_PATH.exists():
            LOG_FILE_PATH.unlink()
    except Exception:
        pass
        

def set_log_level(level: str) -> bool:
    """
    Change Atlas log level at runtime.
    Returns True if successful, False otherwise.
    """
    level = level.upper()

    if not hasattr(logging, level):
        return False

    new_level = getattr(logging, level)

    log.setLevel(new_level)

    for handler in log.handlers:
        handler.setLevel(new_level)

    log.info(f"Log level changed to {level}")
    return True


def get_log_level() -> str:
    return logging.getLevelName(log.level)        
import logging
from pathlib import Path

from config import config


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

_console = logging.StreamHandler()
_console.setFormatter(_formatter)

_file = logging.FileHandler(LOG_FILE_PATH, encoding="utf-8")
_file.setFormatter(_formatter)

_logger.addHandler(_console)
_logger.addHandler(_file)

_logger.propagate = False

# -------------------------------------------------
# Telegram logging
# -------------------------------------------------
_bot = None


def setup(bot):
    global _bot
    _bot = bot


# -------------------------------------------------
# Public API
# -------------------------------------------------
def clear_logs():
    LOG_FILE_PATH.write_text("", encoding="utf-8")


def set_log_level(level: str):
    _logger.setLevel(getattr(logging, level))


def get_log_level() -> str:
    return logging.getLevelName(_logger.level)


def log_event(event: str, details: str = ""):
    message = f"[{event}]"
    if details:
        message += f" {details}"

    _logger.info(message)

    if not _bot:
        return

    chat_id = getattr(config, "LOG_CHAT_ID", None)
    if not chat_id:
        return

    text = f"**{event}**"
    if details:
        text += f"\n{details}"

    try:
        _bot.loop.create_task(
            _bot.send_message(chat_id, text)
        )
    except Exception:
        pass


log = _logger

from datetime import datetime
from telethon import TelegramClient
from utils.logger import log, LOG_FILE_PATH
from log.manager import get_log_chat_id

_bot: TelegramClient | None = None


# -------------------------------------------------
# Setup (called once in run.py)
# -------------------------------------------------
def setup(bot: TelegramClient):
    global _bot
    _bot = bot
    log.info("Telegram logging initialized")


# -------------------------------------------------
# Unified event logger
# -------------------------------------------------
async def log_event(event: str, details: str = ""):
    # -------- File log (via Python logger) --------
    if details:
        log.info(f"[{event}] {details}")
    else:
        log.info(f"[{event}]")

    # -------- Telegram log (optional) --------
    if not _bot:
        return

    chat_id = get_log_chat_id()
    if not chat_id:
        return

    text = f"📌 **{event}**"
    if details:
        text += f"\n{details}"

    try:
        await _bot.send_message(chat_id, text)
    except Exception:
        # Never crash because of logging
        log.exception("Failed to send log event to Telegram")
from pathlib import Path
from telethon import TelegramClient

from log.manager import get_log_chat_id


_bot: TelegramClient | None = None

# -------------------------------------------------
# File logging (manual, minimal, safe)
# -------------------------------------------------
LOG_FILE_PATH = Path("log.txt")


def _write_to_file(text: str):
    try:
        with LOG_FILE_PATH.open("a", encoding="utf-8") as f:
            f.write(text + "\n")
    except Exception:
        pass


def setup(bot: TelegramClient):
    global _bot
    _bot = bot


# -------------------------------------------------
# Telegram log (events / alerts)
# -------------------------------------------------
async def log_event(event: str, details: str = ""):
    text = f"[{event}]"
    if details:
        text += f" {details}"

    # Write ONLY Atlas-level events to file
    _write_to_file(text)

    if not _bot:
        return

    chat_id = get_log_chat_id()
    if not chat_id:
        return

    tg_text = f"📌 **{event}**"
    if details:
        tg_text += f"\n{details}"

    try:
        await _bot.send_message(chat_id, tg_text)
    except Exception:
        pass

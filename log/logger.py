from telethon import TelegramClient
from log.manager import get_log_chat_id


_bot: TelegramClient | None = None


def setup(bot: TelegramClient):
    global _bot
    _bot = bot


async def log_event(event: str, details: str = ""):
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
        # logging must NEVER crash the bot
        pass

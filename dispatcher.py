from telethon.events import NewMessage
import time
import traceback

from config import config
from utils.logger import log_event

# AFK imports
from plugins.system.afk import AFK, clear_afk


PM_RATE_LIMIT = 5
PM_RATE_WINDOW = 60
PM_IGNORE_TIME = 600

_pm_hits = {}
_pm_ignored = {}


def _rate_limited(user_id: int) -> bool:
    now = time.time()

    until = _pm_ignored.get(user_id)
    if until and until > now:
        return True
    elif until:
        _pm_ignored.pop(user_id, None)

    hits = _pm_hits.setdefault(user_id, [])
    hits[:] = [t for t in hits if now - t < PM_RATE_WINDOW]
    hits.append(now)

    if len(hits) > PM_RATE_LIMIT:
        _pm_ignored[user_id] = now + PM_IGNORE_TIME
        _pm_hits.pop(user_id, None)
        return True

    return False


class Dispatcher:
    def __init__(self):
        self.commands = {}

    def register(self, command: str, handler):
        self.commands[command.lower()] = handler

    def bind(self, user, bot=None):
        if user:
            user.add_event_handler(
                self.user_handler,
                NewMessage(outgoing=True),
            )

        if bot:
            bot.add_event_handler(
                self.bot_handler,
                NewMessage(incoming=True),
            )

    async def user_handler(self, event):
        if config.RUN_MODE == "bot":
            return

        text = (event.raw_text or "").strip()

        if AFK.get("enabled"):
            if not text.startswith(".afk"):
                clear_afk()
                log_event("AFK", "I’m back online")

        await self._handle(event, ".")

    async def bot_handler(self, event):
        if config.RUN_MODE == "user":
            return

        if event.is_private:
            if event.sender_id != config.OWNER_ID:
                if _rate_limited(event.sender_id):
                    return

            # Run assistant PM handlers first
            for handler in self.commands.values():
                if getattr(handler, "_assistant_pm", False):
                    try:
                        await handler(event, [])
                    except Exception:
                        log_event(
                            "Assistant Error",
                            traceback.format_exc(limit=6),
                        )

            # Owner can still run commands
            if event.sender_id == config.OWNER_ID:
                await self._handle(event, "/")
            return

        if event.sender_id == config.OWNER_ID:
            await self._handle(event, "/")

    async def _handle(self, event, prefix):
        text = event.raw_text or ""
        if not text.startswith(prefix):
            return

        parts = text[len(prefix):].strip().split()
        if not parts:
            return

        command = parts[0].lower()
        args = parts[1:]

        handler = self.commands.get(command)
        if not handler:
            return

        try:
            await handler(event, args)
        except Exception as e:
            log_event(
                "Command Error",
                f"{event.raw_text}\n{type(e).__name__}: {e}",
            )


dispatcher = Dispatcher()

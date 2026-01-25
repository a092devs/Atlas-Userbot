from telethon.events import NewMessage

from config import config
from utils.logger import log
from log.logger import log_event

# AFK imports
from plugins.system.afk import AFK, clear_afk


class Dispatcher:
    def __init__(self):
        self.commands = {}

    # -------------------------------------------------
    # Register commands
    # -------------------------------------------------
    def register(self, command: str, handler):
        self.commands[command.lower()] = handler

    # -------------------------------------------------
    # Bind clients
    # -------------------------------------------------
    def bind(self, user, bot=None):
        if user:
            # Userbot: ONLY outgoing messages
            user.add_event_handler(
                self.user_handler,
                NewMessage(outgoing=True),
            )

        if bot:
            # Assistant bot: ONLY incoming messages
            bot.add_event_handler(
                self.bot_handler,
                NewMessage(incoming=True),
            )

    # -------------------------------------------------
    # USERBOT HANDLER (.)
    # -------------------------------------------------
    async def user_handler(self, event):
        # In bot mode, userbot must stay silent
        if config.RUN_MODE == "bot":
            return

        text = (event.raw_text or "").strip()

        # -------------------------------------------------
        # AFK AUTO-DISABLE (THIS IS THE KEY FIX)
        # -------------------------------------------------
        if AFK.get("enabled"):
            # Ignore the AFK command itself
            if not text.startswith(".afk"):
                clear_afk()
                await log_event(
                    event="AFK",
                    details="I’m back online",
                )

        await self._handle(event, prefix=".")

    # -------------------------------------------------
    # ASSISTANT BOT HANDLER (/)
    # -------------------------------------------------
    async def bot_handler(self, event):
        # Only owner can control assistant
        if event.sender_id != config.OWNER_ID:
            return

        # In user mode, assistant bot must stay silent
        if config.RUN_MODE == "user":
            return

        await self._handle(event, prefix="/")

    # -------------------------------------------------
    # CORE DISPATCH LOGIC (COMMANDS ONLY)
    # -------------------------------------------------
    async def _handle(self, event, prefix: str):
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
            log.error(f"Unhandled exception in '{command}': {e}")

            await log_event(
                event="Command Error",
                details=f"{event.raw_text}\n{type(e).__name__}: {e}",
            )


dispatcher = Dispatcher()

from typing import Callable, Awaitable
from telethon import events
from telethon.events import NewMessage

from config import config
from utils.logger import log
from log.logger import log_event


Handler = Callable[[events.NewMessage.Event, list[str]], Awaitable[None]]


class Dispatcher:
    def __init__(self):
        self.commands: dict[str, Handler] = {}

    def register(self, command: str, handler: Handler):
        self.commands[command.lower()] = handler
        log.debug(f"Registered command: {command}")

    async def _handle(self, event, prefix: str, source: str):
        """
        source = 'user' | 'bot'
        """
        # Mode filtering
        if config.RUN_MODE == "user" and source != "user":
            return
        if config.RUN_MODE == "bot" and source != "bot":
            return

        text = event.raw_text or ""
        if not text.startswith(prefix):
            return

        parts = text[len(prefix):].split()
        if not parts:
            return

        cmd, args = parts[0].lower(), parts[1:]
        handler = self.commands.get(cmd)
        if not handler:
            return

        try:
            await handler(event, args)
        except Exception as e:
            await log_event(
                event="Command Error",
                details=f"{command} {args}\n{e}",
            )

    def bind(self, user_client, bot_client):
        if user_client:

            @user_client.on(NewMessage)
            async def user_handler(event):
                await self._handle(event, ".", source="user")

        if bot_client:

            @bot_client.on(NewMessage)
            async def bot_handler(event):
                await self._handle(event, "/", source="bot")

        log.info(f"Dispatcher bound (mode={config.RUN_MODE})")


dispatcher = Dispatcher()

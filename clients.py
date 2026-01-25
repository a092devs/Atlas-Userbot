from telethon import TelegramClient
from telethon.sessions import StringSession

from config import config
from utils.logger import log


class Clients:
    def __init__(self):
        self.user: TelegramClient | None = None
        self.bot: TelegramClient | None = None

    async def start(self):
        """
        Start user and/or bot clients depending on config.
        """

        # ---------------- Userbot ----------------
        if config.STRING_SESSION:
            log.info("Starting userbot")
            self.user = TelegramClient(
                StringSession(config.STRING_SESSION),
                config.API_ID,
                config.API_HASH,
            )
            await self.user.start()
            log.info("Userbot started")

        # ---------------- Assistant Bot ----------------
        if config.BOT_TOKEN:
            log.info("Starting bot")
            self.bot = TelegramClient(
                "assistant-bot",
                config.API_ID,
                config.API_HASH,
            )
            await self.bot.start(bot_token=config.BOT_TOKEN)
            log.info("Bot started")

        # ---------------- Validation ----------------
        if not self.user and not self.bot:
            raise RuntimeError(
                "No clients configured. "
                "Provide STRING_SESSION and/or BOT_TOKEN."
            )


clients = Clients()

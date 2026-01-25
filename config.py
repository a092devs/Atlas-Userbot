import os
from dotenv import load_dotenv

load_dotenv()


class ConfigError(RuntimeError):
    pass


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ConfigError(f"Missing required config value: {name}")
    return value


class Config:
    # -------- Telegram credentials --------
    API_ID = int(_require("API_ID"))
    API_HASH = _require("API_HASH")

    # -------- Runtime mode --------
    RUN_MODE = os.getenv("RUN_MODE", "dual").lower()
    if RUN_MODE not in ("user", "bot", "dual"):
        raise ConfigError("RUN_MODE must be one of: user, bot, dual")

    # -------- Userbot --------
    STRING_SESSION = os.getenv("STRING_SESSION", "")

    # -------- Assistant bot --------
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")

    # Validate required values based on mode
    if RUN_MODE in ("user", "dual") and not STRING_SESSION:
        raise ConfigError("STRING_SESSION is required for user or dual mode")

    if RUN_MODE in ("bot", "dual") and not BOT_TOKEN:
        raise ConfigError("BOT_TOKEN is required for bot or dual mode")

    # -------- Owner --------
    OWNER_ID = int(_require("OWNER_ID"))

    # -------- Paths & storage --------
    DB_FILE = os.getenv("DB_FILE", "atlas.db")
    PLUGIN_PATH = os.getenv("PLUGIN_PATH", "plugins")

    # -------- Logging --------
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # -------- Environment --------
    ENV = os.getenv("ENV", "production")
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"


config = Config()

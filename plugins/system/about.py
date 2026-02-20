import sys
import time
import platform

from utils.respond import respond
from config import config
from dispatcher import dispatcher

try:
    import telethon
    TELETHON_VERSION = telethon.__version__
except Exception:
    TELETHON_VERSION = "Unknown"


__plugin__ = {
    "name": "About",
    "category": "system",
    "description": (
        "Show core information about Atlas.\n\n"
        "Usage:\n"
        "`.about`"
    ),
    "commands": {
        "about": "Show system and runtime information",
    },
}


# Track start time when module loads
START_TIME = time.time()

REPO_URL = "https://github.com/a092devs/Atlas-Userbot"


def format_uptime():
    seconds = int(time.time() - START_TIME)

    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    return f"{days}d {hours}h {minutes}m {seconds}s"


async def handler(event, args):
    uptime = format_uptime()

    python_version = sys.version.split()[0]
    os_info = platform.system()

    plugin_count = len(dispatcher.commands)

    text = (
        "<b>Atlas Userbot</b>\n\n"
        f"<b>Run Mode:</b> {config.RUN_MODE}\n"
        f"<b>Owner ID:</b> {config.OWNER_ID}\n"
        f"<b>Plugins Loaded:</b> {plugin_count}\n"
        f"<b>Uptime:</b> {uptime}\n\n"
        f"<b>Python:</b> {python_version}\n"
        f"<b>Telethon:</b> {TELETHON_VERSION}\n"
        f"<b>OS:</b> {os_info}\n\n"
        f"<a href='{REPO_URL}'>Repository</a>"
    )

    await respond(event, text)
import sys
import time
import platform

from utils.respond import respond
from dispatcher import dispatcher


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


START_TIME = time.time()
REPO_URL = "https://github.com/a092devs/Atlas-Userbot"
OWNER_USERNAME = "https://t.me/a092devs"


def format_uptime():
    seconds = int(time.time() - START_TIME)

    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    return f"{days}d {hours}h {minutes}m {seconds}s"


def get_telethon_version():
    try:
        import telethon
        return telethon.__version__
    except Exception:
        return "Unknown"


async def handler(event, args):
    uptime = format_uptime()
    python_version = sys.version.split()[0]
    os_info = platform.system()

    plugin_count = len(set(dispatcher.commands.values()))

    text = (
        "**System Information**\n\n"
        f"**Owner:** [@a092devs]({OWNER_USERNAME})\n"
        f"**Plugins Loaded:** `{plugin_count}`\n"
        f"**Uptime:** `{uptime}`\n\n"
        f"**Python:** `{python_version}`\n"
        f"**Telethon:** `{get_telethon_version()}`\n"
        f"**OS:** `{os_info}`\n\n"
        f"[Atlas Userbot]({REPO_URL})"
    )

    await respond(event, text)
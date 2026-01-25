import time

from core.version import get_version
from utils.formatting import human_time
from utils.respond import respond


__plugin__ = {
    "name": "Alive",
    "category": "system",
    "description": "Check bot status, uptime and version",
    "commands": {
        "alive": "Show bot status, uptime, version and running mode",
    },
}


# -------------------------------------------------
# START_TIME fallback
# -------------------------------------------------
try:
    from run import START_TIME
except Exception:
    START_TIME = time.time()


async def handler(event, args):
    version, codename = get_version()
    uptime = human_time(time.time() - START_TIME)

    # Atlas-correct mode detection
    mode = "User" if event.out else "Bot"

    text = (
        "🤖 **Atlas is Alive**\n\n"
        f"• **Version:** `{version}` ({codename})\n"
        f"• **Uptime:** `{uptime}`\n"
        f"• **Mode:** `{mode}`\n"
        f"• **Status:** ✅ Running"
    )

    await respond(event, text)

import time

from utils.respond import respond
from log.logger import log_event


__plugin__ = {
    "name": "AFK",
    "category": "system",
    "description": "Tell others you are away from keyboard",
    "commands": {
        "afk": "Set AFK status with optional reason",
    },
}


AFK = {
    "enabled": False,
    "since": None,
    "reason": None,
}


def set_afk(reason: str | None):
    AFK["enabled"] = True
    AFK["since"] = time.time()
    AFK["reason"] = reason


def clear_afk():
    AFK["enabled"] = False
    AFK["since"] = None
    AFK["reason"] = None


async def handler(event, args):
    if AFK["enabled"]:
        return await respond(event, "ℹ️ You’re already AFK.")

    reason = " ".join(args) if args else None
    set_afk(reason)

    await log_event(
        event="AFK",
        details="I’m AFK now" + (f" — {reason}" if reason else ""),
    )

    text = "😴 **I’m AFK now**"
    if reason:
        text += f"\n💬 **Reason:** {reason}"

    await respond(event, text)

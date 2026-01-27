from utils.respond import respond
from config import config
from utils.logger import log_event

from db import apikeys as apikeys_db


__plugin__ = {
    "name": "APIKeys",
    "category": "system",
    "description": "Manage API keys used by plugins",
    "commands": {
        "setapi": "Set an API key (owner only)",
        "delapi": "Delete an API key",
        "listapi": "List configured API keys",
    },
}


# 🔑 AUTO-CALLED BY LOADER
def init():
    apikeys_db.init()


def is_owner(event):
    return event.sender_id == config.OWNER_ID


async def handler(event, args):
    if not is_owner(event):
        return

    cmd = event.raw_text.split()[0].lstrip("./").lower()

    # ---------------- setapi ----------------
    if cmd == "setapi":
        if len(args) < 2:
            return await respond(
                event,
                "❌ Usage:\n"
                "`.setapi <KEY_NAME> <KEY_VALUE>`",
            )

        name = args[0].upper()
        value = " ".join(args[1:])

        apikeys_db.set_key(name, value)

        log_event(
            event="API key set",
            details=f"Key: {name}",
        )

        await respond(
            event,
            f"✅ API key `{name}` saved successfully.",
        )

    # ---------------- delapi ----------------
    elif cmd == "delapi":
        if not args:
            return await respond(event, "❌ Usage: `.delapi <KEY_NAME>`")

        name = args[0].upper()
        apikeys_db.delete_key(name)

        log_event(
            event="API key deleted",
            details=f"Key: {name}",
        )

        await respond(event, f"🗑 API key `{name}` deleted.")

    # ---------------- listapi ----------------
    elif cmd == "listapi":
        keys = apikeys_db.list_keys()
        if not keys:
            return await respond(event, "ℹ️ No API keys configured.")

        text = "🔑 **Configured API Keys**\n\n"
        for k in keys:
            text += f"• `{k}`\n"

        await respond(event, text)

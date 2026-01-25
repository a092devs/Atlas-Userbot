from utils.respond import respond
from config import config
from db.apikeys import set_key, delete_key, list_keys
from log.logger import log_event
from utils.human import format_user


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


def is_owner(event):
    return event.sender_id == config.OWNER_ID


async def handler(event, args):
    if not is_owner(event):
        return

    user = await format_user(event)
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

        set_key(name, value)

        await log_event(
            event="API key set",
            details=f"Key: {name}\nBy: {user}",
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
        delete_key(name)

        await log_event(
            event="API key deleted",
            details=f"Key: {name}\nBy: {user}",
        )

        await respond(event, f"🗑 API key `{name}` deleted.")

    # ---------------- listapi ----------------
    elif cmd == "listapi":
        keys = list_keys()
        if not keys:
            return await respond(event, "ℹ️ No API keys configured.")

        text = "🔑 **Configured API Keys**\n\n"
        for k in keys:
            text += f"• `{k}`\n"

        await respond(event, text)

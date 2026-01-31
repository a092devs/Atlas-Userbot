from telethon.errors import YouBlockedUserError

from dispatcher import dispatcher
from utils.respond import respond
from utils.logger import log_event


__plugin__ = {
    "name": "Xiaomi",
    "category": "utils",
    "description": "Fetch Xiaomi device information via XiaomiGeeksBot",
    "commands": {
        "fw": "Get firmware info",
        "vendor": "Get vendor image",
        "specs": "Get device specs",
        "fastboot": "Get fastboot ROM",
        "recovery": "Get recovery ROM",
        "of": "Get OrangeFox recovery",
        "latest": "Get latest OS info",
        "archive": "Get official ROM archive",
        "eu": "Get Xiaomi.eu ROM",
        "twrp": "Get TWRP recovery",
        "models": "Get device models",
        "whatis": "Get device name from codename",
    },
}

XIAOMI_BOT = "XiaomiGeeksBot"


# -------------------------------------------------
# Conversation helper (NO SPAM)
# -------------------------------------------------

async def _xiaomi_conv(event, query: str, loading_text: str):
    client = event.client

    # Edit the original command message (KEEP THIS)
    status_msg = await event.edit(loading_text)

    try:
        async with client.conversation(XIAOMI_BOT, timeout=15) as conv:
            # Send message to Xiaomi bot
            sent = await conv.send_message(query)

            # Receive reply
            reply = await conv.get_response(timeout=10)

            # Forward reply to current chat
            await client.forward_messages(
                event.chat_id,
                reply.id,
                XIAOMI_BOT,
            )

            # 🔥 Cleanup ONLY bot-side messages
            await client.delete_messages(
                XIAOMI_BOT,
                [sent.id, reply.id],
            )

            # ❗ Do NOT delete or edit status_msg anymore

    except YouBlockedUserError:
        await status_msg.edit("Please unblock @XiaomiGeeksBot first.")

    except Exception as e:
        log_event("Xiaomi Error", str(e))
        await status_msg.edit("Failed to fetch data.")


# -------------------------------------------------
# Command handler
# -------------------------------------------------

async def handler(event, args):
    if not args:
        return await respond(event, "Usage: .<command> <codename>")

    cmd = event.raw_text.lstrip("./").split()[0].lower()
    codename = args[0]

    # fw is userbot alias → bot MUST get /firmware
    if cmd == "fw":
        return await _xiaomi_conv(
            event,
            f"/firmware {codename}",
            "Fetching firmware info…",
        )

    mapping = {
        "vendor": "/vendor",
        "specs": "/specs",
        "fastboot": "/fastboot",
        "recovery": "/recovery",
        "of": "/of",
        "latest": "/latest",
        "archive": "/archive",
        "eu": "/eu",
        "twrp": "/twrp",
        "models": "/models",
        "whatis": "/whatis",
    }

    if cmd in mapping:
        return await _xiaomi_conv(
            event,
            f"{mapping[cmd]} {codename}",
            f"Fetching {cmd} info…",
        )


# -------------------------------------------------
# Register commands
# -------------------------------------------------

dispatcher.register("fw", handler)
dispatcher.register("vendor", handler)
dispatcher.register("specs", handler)
dispatcher.register("fastboot", handler)
dispatcher.register("recovery", handler)
dispatcher.register("of", handler)
dispatcher.register("latest", handler)
dispatcher.register("archive", handler)
dispatcher.register("eu", handler)
dispatcher.register("twrp", handler)
dispatcher.register("models", handler)
dispatcher.register("whatis", handler)

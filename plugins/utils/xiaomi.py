import asyncio

from telethon.errors import YouBlockedUserError
from telethon.tl.functions.messages import ForwardMessagesRequest

from utils.logger import log_event


__plugin__ = {
    "name": "Xiaomi",
    "category": "utils",
    "description": "Xiaomi device info via @XiaomiGeeksBot",
    "commands": {
        "fw": "Get latest firmware",
        "vendor": "Get latest vendor",
        "specs": "Get device specs",
        "fastboot": "Get fastboot ROM",
        "recovery": "Get recovery ROM",
        "of": "Get OrangeFox recovery",
        "latest": "Get latest OS info",
        "archive": "Get official ROM archive",
        "eu": "Get Xiaomi.eu ROMs",
        "twrp": "Get TWRP recovery",
        "models": "Get device models",
        "whatis": "Get device name from codename",
    },
}

XIAOMI_BOT = "XiaomiGeeksBot"


# -------------------------------------------------
# Core helper
# -------------------------------------------------

async def _xiaomi_request(
    event,
    bot_command: str,
    codename: str,
    loading_text: str,
):
    try:
        # Edit original command message
        await event.edit(loading_text)

        async with event.client.conversation(
            XIAOMI_BOT, timeout=20
        ) as conv:
            await conv.send_message(f"/{bot_command} {codename}")
            response = await conv.get_response()

        # Forward bot reply
        await event.client(
            ForwardMessagesRequest(
                from_peer=XIAOMI_BOT,
                id=[response.id],
                to_peer=event.chat_id,
            )
        )

        # Remove loading message
        await event.delete()

    except YouBlockedUserError:
        await event.edit("Please unblock @XiaomiGeeksBot first.")
    except asyncio.TimeoutError:
        await event.edit("No response from XiaomiGeeksBot.")
    except Exception as e:
        log_event("Xiaomi Error", str(e))
        await event.edit("Failed to fetch data.")


# -------------------------------------------------
# Command handler
# -------------------------------------------------

async def handler(event, args):
    if not args:
        return await event.edit("Usage: .fw <codename>")

    user_cmd = event.raw_text.split()[0].lstrip("./").lower()
    codename = args[0]

    # Map USER command → BOT command
    bot_command_map = {
        "fw": "firmware",
        "vendor": "vendor",
        "specs": "specs",
        "fastboot": "fastboot",
        "recovery": "recovery",
        "of": "of",
        "latest": "latest",
        "archive": "archive",
        "eu": "eu",
        "twrp": "twrp",
        "models": "models",
        "whatis": "whatis",
    }

    loading_messages = {
        "fw": "Fetching firmware info…",
        "vendor": "Fetching vendor info…",
        "specs": "Fetching device specs…",
        "fastboot": "Fetching fastboot ROM…",
        "recovery": "Fetching recovery ROM…",
        "of": "Fetching OrangeFox recovery…",
        "latest": "Fetching latest OS info…",
        "archive": "Fetching archive links…",
        "eu": "Fetching Xiaomi.eu ROMs…",
        "twrp": "Fetching TWRP recovery…",
        "models": "Fetching models…",
        "whatis": "Identifying device…",
    }

    bot_cmd = bot_command_map.get(user_cmd)
    loading = loading_messages.get(user_cmd)

    if not bot_cmd or not loading:
        return

    await _xiaomi_request(
        event,
        bot_command=bot_cmd,
        codename=codename,
        loading_text=loading,
    )

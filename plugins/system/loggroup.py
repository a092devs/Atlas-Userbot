from log.manager import (
    init as init_log_manager,
    get_log_chat_id,
    set_log_chat_id,
    remove_log_chat_id,
)
from utils.respond import respond
from config import config


__plugin__ = {
    "name": "LogGroup",
    "category": "system",
    "description": "Manage where Atlas sends its logs",
    "commands": {
        "setlog": "Set the current chat as the log group",
        "dellog": "Remove the configured log group",
        "logstatus": "Show the currently configured log group",
        "testlog": "Send a test log message to the log group",
    },
}


# 🔑 called automatically by loader
def init():
    init_log_manager()


def is_owner(event):
    return event.sender_id == config.OWNER_ID


async def handler(event, args):
    if not is_owner(event):
        return  # stay silent for non-owner

    cmd = event.raw_text.split()[0].lstrip("./").lower()

    if cmd == "setlog":
        chat_id = event.chat_id
        set_log_chat_id(chat_id)
        return await respond(
            event,
            "✅ **Log group configured successfully**\n\n"
            f"**Chat ID:** `{chat_id}`",
        )

    if cmd == "dellog":
        remove_log_chat_id()
        return await respond(event, "🗑 **Log group removed**")

    if cmd == "logstatus":
        cid = get_log_chat_id()
        if not cid:
            return await respond(event, "ℹ️ No log group configured.")
        return await respond(
            event,
            "📌 **Current log group**\n\n"
            f"`{cid}`",
        )

    if cmd == "testlog":
        cid = get_log_chat_id()
        if not cid:
            return await respond(event, "❌ No log group configured.")

        try:
            await event.client.send_message(
                cid,
                "🧪 **Atlas test log message**",
            )
            return await respond(event, "✅ Test log sent successfully.")
        except Exception as e:
            return await respond(
                event,
                "❌ Failed to send test log message:\n"
                f"`{e}`",
            )

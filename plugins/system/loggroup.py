from utils.respond import respond
from config import config
from utils.logger import log_event, clear_logs
from db.control import (
    set_log_chat_id,
    get_log_chat_id,
    clear_log_chat_id,
)


__plugin__ = {
    "name": "LogGroup",
    "category": "system",
    "description": "Manage where Atlas sends its logs",
    "commands": {
        # canonical commands
        "setlog": "Set the current chat as the log group",
        "dellog": "Remove the configured log group",
        "logstatus": "Show the currently configured log group",
        "testlog": "Send a test log message to the log group",
        "clearlog": "Clear stored log file",

        # UX alias
        "loggroup": "Manage log group (set, del, status, test, clear)",
    },
}


def is_owner(event):
    return event.sender_id == config.OWNER_ID


async def handler(event, args):
    if not is_owner(event):
        return

    raw = event.raw_text.strip().lstrip("./")
    parts = raw.split()
    cmd = parts[0].lower()
    sub = parts[1].lower() if len(parts) > 1 else None

    # -------------------------------------------------
    # loggroup alias router
    # -------------------------------------------------
    if cmd == "loggroup":
        if sub in ("set", None):
            set_log_chat_id(event.chat_id)
            await respond(
                event,
                "Log group configured successfully.\n\n"
                f"Chat ID: `{event.chat_id}`",
            )
            log_event(
                event="Log group updated",
                details=f"New log chat: {event.chat_id}",
            )
            return

        if sub in ("del", "remove"):
            clear_log_chat_id()
            await respond(event, "Log group removed.")
            log_event(
                event="Log group removed",
                details="Telegram logging disabled",
            )
            return

        if sub in ("status", "show"):
            chat_id = get_log_chat_id()
            if not chat_id:
                return await respond(event, "No log group configured.")
            return await respond(
                event,
                "Current log group:\n\n"
                f"`{chat_id}`",
            )

        if sub == "test":
            if not get_log_chat_id():
                return await respond(event, "No log group configured.")
            log_event(
                event="Test log",
                details="This is a test log message from Atlas",
            )
            return await respond(event, "Test log sent successfully.")

        if sub == "clear":
            clear_logs()
            log_event(
                event="Logs cleared",
                details="Log file cleared via command",
            )
            return await respond(event, "Log file cleared successfully.")

        return await respond(
            event,
            "Usage:\n"
            "`.loggroup set`\n"
            "`.loggroup del`\n"
            "`.loggroup status`\n"
            "`.loggroup test`\n"
            "`.loggroup clear`",
        )

    # -------------------------------------------------
    # legacy flat commands (still supported)
    # -------------------------------------------------
    if cmd == "setlog":
        set_log_chat_id(event.chat_id)
        await respond(
            event,
            "Log group configured successfully.\n\n"
            f"Chat ID: `{event.chat_id}`",
        )
        log_event(
            event="Log group updated",
            details=f"New log chat: {event.chat_id}",
        )
        return

    if cmd == "dellog":
        clear_log_chat_id()
        await respond(event, "Log group removed.")
        log_event(
            event="Log group removed",
            details="Telegram logging disabled",
        )
        return

    if cmd == "logstatus":
        chat_id = get_log_chat_id()
        if not chat_id:
            return await respond(event, "No log group configured.")
        return await respond(
            event,
            "Current log group:\n\n"
            f"`{chat_id}`",
        )

    if cmd == "testlog":
        if not get_log_chat_id():
            return await respond(event, "No log group configured.")
        log_event(
            event="Test log",
            details="This is a test log message from Atlas",
        )
        return await respond(event, "Test log sent successfully.")

    if cmd == "clearlog":
        clear_logs()
        log_event(
            event="Logs cleared",
            details="Log file cleared via command",
        )
        return await respond(event, "Log file cleared successfully.")

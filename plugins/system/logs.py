from pathlib import Path
from io import BytesIO

from utils.respond import respond
from config import config
from log.logger import log_event, LOG_FILE_PATH
from utils.logger import clear_logs, set_log_level, get_log_level

__plugin__ = {
    "name": "Logs",
    "category": "system",
    "description": "View, clear or control Atlas logs",
    "commands": {
        "log": "Upload Atlas logs or last N lines",
        "clearlog": "Clear Atlas log file",
        "loglevel": "Get or set Atlas log level",
    },
}


def is_owner(event):
    return event.sender_id == config.OWNER_ID


def tail_lines(path: Path, lines: int) -> str:
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        return "".join(f.readlines()[-lines:])


async def handler(event, args):
    if not is_owner(event):
        return

    text = (event.raw_text or "").strip()
    
    # -------------------------------------------------
    # .loglevel
    # -------------------------------------------------
    if text.startswith(".loglevel") or text.startswith("/loglevel"):
        # .loglevel → show current
        if not args:
            current = get_log_level()
            return await respond(
                event,
                f"📊 **Current log level:** `{current}`\n\n"
                "**Available levels:**\n"
                "`debug`, `info`, `warning`, `error`, `critical`",
            )

        level = args[0].lower()

        if not set_log_level(level):
            return await respond(
                event,
                "❌ **Invalid log level.**\n\n"
                "Valid levels:\n"
                "`debug`, `info`, `warning`, `error`, `critical`",
            )

        await respond(
            event,
            f"✅ **Log level set to `{level.upper()}`**",
        )

        await log_event(
            event="Log Level Changed",
            details=f"New level: {level.upper()}",
        )
        return

    # -------------------------------------------------
    # .clearlog
    # -------------------------------------------------
    if text in (".clearlog", "/clearlog"):
        clear_logs()

        await respond(event, "🧹 **Logs cleared successfully.**")

        await log_event(
            event="Logs Cleared",
            details="Log file was manually cleared",
        )
        return

    # -------------------------------------------------
    # .log <n>
    # -------------------------------------------------
    if args and args[0].isdigit():
        if not LOG_FILE_PATH.exists():
            return await respond(event, "ℹ️ Log file is empty.")

        lines = int(args[0])
        content = tail_lines(LOG_FILE_PATH, lines)

        if not content.strip():
            return await respond(event, "ℹ️ Log file is empty.")

        bio = BytesIO(content.encode())
        bio.name = f"atlas-log-last-{lines}.txt"

        await event.client.send_file(
            event.chat_id,
            file=bio,
            caption=f"📄 **Last {lines} lines of Atlas log**",
        )

        await log_event(
            event="Log Uploaded",
            details=f"Last {lines} lines uploaded",
        )
        return

    # -------------------------------------------------
    # .log (full)
    # -------------------------------------------------
    if not args:
        if not LOG_FILE_PATH.exists():
            return await respond(event, "ℹ️ Log file is empty.")

        await event.client.send_file(
            event.chat_id,
            file=LOG_FILE_PATH,
            filename="atlas-log.txt",
            caption="📄 **Atlas Log File**",
        )

        await log_event(
            event="Log Uploaded",
            details="Full log uploaded",
        )
        return

    # -------------------------------------------------
    # invalid usage
    # -------------------------------------------------
    await respond(
        event,
        "❌ **Usage:**\n"
        "`.log` – upload full log file\n"
        "`.log <lines>` – upload last N lines\n"
        "`.clearlog` – clear log file\n\n"
        "**Examples:**\n"
        "`.log`\n"
        "`.log 20`\n"
        "`.clearlog`",
    )
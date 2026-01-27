from pathlib import Path
from io import BytesIO
import logging

from utils.respond import respond
from config import config
from utils.logger import log_event
from utils.logger import LOG_FILE_PATH, clear_logs, set_log_level, get_log_level


__plugin__ = {
    "name": "Logs",
    "category": "system",
    "description": "View, clear, or control Atlas logging",
    "commands": {
        "log": "Upload Atlas logs or last N lines",
        "clearlog": "Clear Atlas log file",
        "loglevel": "Get or set Atlas log verbosity",
    },
}


# -------------------------------------------------
# Helpers
# -------------------------------------------------
def is_owner(event):
    return event.sender_id == config.OWNER_ID


def tail_lines(path: Path, lines: int) -> str:
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        return "".join(f.readlines()[-lines:])


LOG_LEVEL_HELP = (
    "🧾 **Log Level Control**\n\n"
    "Control how much information Atlas logs.\n\n"
    "**Available levels:**\n"
    "• **ERROR** – Only errors and crashes\n"
    "• **WARNING** – Errors and important warnings\n"
    "• **INFO** – Normal operation *(default)*\n"
    "• **DEBUG** – Very verbose, for debugging\n"
    "• **CRITICAL** – Fatal errors only\n\n"
    "**Usage:**\n"
    "• `.loglevel` → show current log level\n"
    "• `.loglevel <level>` → set log level\n\n"
    "**Examples:**\n"
    "• `.loglevel info`\n"
    "• `.loglevel debug`\n"
    "• `.loglevel error`"
)


# -------------------------------------------------
# Command handler
# -------------------------------------------------
async def handler(event, args):
    if not is_owner(event):
        return

    text = (event.raw_text or "").strip()

    # -------------------------------------------------
    # .clearlog
    # -------------------------------------------------
    if text in (".clearlog", "/clearlog"):
        clear_logs()

        await respond(event, "🧹 **Logs cleared successfully.**")

        log_event(
            event="Logs Cleared",
            details="Log file was manually cleared",
        )
        return

    # -------------------------------------------------
    # .loglevel
    # -------------------------------------------------
    if text.startswith((".loglevel", "/loglevel")):
        if not args:
            await respond(
                event,
                f"📊 **Current log level:** `{get_log_level()}`\n\n{LOG_LEVEL_HELP}",
            )
            return

        level_name = args[0].upper()
        if not hasattr(logging, level_name):
            await respond(
                event,
                "❌ **Invalid log level.**\n\n" + LOG_LEVEL_HELP,
            )
            return

        set_log_level(level_name)

        await respond(event, f"✅ **Log level set to `{level_name}`**")

        log_event(
            event="Log Level Changed",
            details=f"New level: {level_name}",
        )
        return

    # -------------------------------------------------
    # .log <n>
    # -------------------------------------------------
    if args and args[0].isdigit():
        if (
            not LOG_FILE_PATH.exists()
            or LOG_FILE_PATH.stat().st_size == 0
        ):
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
        return

    # -------------------------------------------------
    # .log (full)
    # -------------------------------------------------
    if text in (".log", "/log"):
        if (
            not LOG_FILE_PATH.exists()
            or LOG_FILE_PATH.stat().st_size == 0
        ):
            return await respond(event, "ℹ️ Log file is empty.")

        await event.client.send_file(
            event.chat_id,
            file=LOG_FILE_PATH,
            filename="atlas-log.txt",
            caption="📄 **Atlas Log File**",
        )
        return

    # -------------------------------------------------
    # fallback help
    # -------------------------------------------------
    await respond(event, LOG_LEVEL_HELP)
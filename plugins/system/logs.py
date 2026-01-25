from pathlib import Path
from io import BytesIO

from utils.respond import respond
from config import config
from log.logger import log_event, LOG_FILE_PATH


__plugin__ = {
    "name": "Logs",
    "category": "system",
    "description": "Upload Atlas log file",
    "commands": {
        "log": "Upload Atlas logs or last N lines",
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

    if not LOG_FILE_PATH.exists():
        return await respond(event, "❌ Log file not found.")

    # ---------------- .log <n> ----------------
    if args and args[0].isdigit():
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

    # ---------------- .log ----------------
    if not args:
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

    # ---------------- invalid usage ----------------
    await respond(
        event,
        "❌ **Usage:**\n"
        "`.log` – upload full log file\n"
        "`.log <lines>` – upload last N lines\n\n"
        "**Examples:**\n"
        "`.log`\n"
        "`.log 20`",
    )

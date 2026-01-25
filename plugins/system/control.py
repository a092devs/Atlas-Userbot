import os
import sys
import asyncio
import subprocess
from pathlib import Path

from config import config
from utils.respond import respond
from log.logger import log_event
from db.control import set_action
from utils.human import format_user


__plugin__ = {
    "name": "Control",
    "category": "system",
    "description": "Restart or update the userbot safely",
    "commands": {
        "restart": "Restart Atlas safely",
        "update": "Check for updates or update Atlas from GitHub",
    },
}


REPO_URL = "https://github.com/a092devs/Atlas-Userbot"
GIT_DIR = Path(".git")


# -------------------------------------------------
# Helpers
# -------------------------------------------------
def is_owner(event):
    return event.sender_id == config.OWNER_ID


def run_git(cmd: list[str]) -> str:
    return subprocess.check_output(
        cmd,
        stderr=subprocess.STDOUT,
        text=True,
    ).strip()


def ensure_git_repo():
    return GIT_DIR.exists()


def get_local_commit():
    return run_git(["git", "rev-parse", "HEAD"])


def get_remote_commit():
    run_git(["git", "fetch", "origin"])
    return run_git(["git", "rev-parse", "origin/HEAD"])


def get_changelog():
    return run_git(
        ["git", "log", "--oneline", "HEAD..origin/HEAD"]
    )


# -------------------------------------------------
# Handler
# -------------------------------------------------
async def handler(event, args):
    user = await format_user(event)

    if not is_owner(event):
        return await respond(event, "❌ You are not allowed to use this command.")

    if config.RUN_MODE == "bot":
        return await respond(event, "⚠️ Control disabled in BOT mode.")

    if not ensure_git_repo():
        return await respond(
            event,
            "❌ Git repository not found.\n"
            "Atlas must be cloned from GitHub to use update.",
        )

    cmd = event.raw_text.split()[0].lstrip("./").lower()
    sub = args[0].lower() if args else None

    chat_id = event.chat_id
    message_id = event.id

    # -------------------------------------------------
    # RESTART
    # -------------------------------------------------
    if cmd == "restart":
        await respond(event, "🔄 **Restarting Atlas…**")

        set_action(
            action="restart",
            chat_id=chat_id,
            message_id=message_id,
        )

        await log_event("Restart Initiated", f"By {user}")
        await asyncio.sleep(1)

        os.execv(sys.executable, [sys.executable] + sys.argv)

    # -------------------------------------------------
    # UPDATE
    # -------------------------------------------------
    if cmd == "update":
        # Step 1: check updates
        if sub != "now":
            await respond(event, "🔍 **Checking for updates…**")

            try:
                local = get_local_commit()
                remote = get_remote_commit()
            except Exception as e:
                return await respond(event, f"❌ Git error:\n`{e}`")

            if local == remote:
                return await respond(
                    event,
                    "✅ **Atlas is already up to date**",
                )

            changelog = get_changelog()
            if not changelog:
                changelog = "_No changelog available_"

            return await respond(
                event,
                "⬆️ **Update Available!**\n\n"
                "📝 **Changelog:**\n"
                f"```\n{changelog}\n```\n"
                "Run `.update now` to apply the update.",
            )

        # Step 2: apply update
        await respond(event, "⬇️ **Updating Atlas…**")

        set_action(
            action="update",
            chat_id=chat_id,
            message_id=message_id,
        )

        await log_event("Update Initiated", f"By {user}")

        try:
            run_git(["git", "pull", "--ff-only"])
        except Exception as e:
            return await respond(event, f"❌ Update failed:\n`{e}`")

        await asyncio.sleep(1)
        os.execv(sys.executable, [sys.executable] + sys.argv)

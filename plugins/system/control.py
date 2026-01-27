import os
import sys
import asyncio
import subprocess
from pathlib import Path

from config import config
from utils.respond import respond
from utils.logger import log_event
from db.control import set_action


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
    if not GIT_DIR.exists():
        raise RuntimeError("Not a git repository")
    return run_git(["git", "rev-parse", "HEAD"])


def get_remote_commit():
    run_git(["git", "fetch", "origin"])
    return run_git(["git", "rev-parse", "origin/HEAD"])


def get_changelog():
    raw = run_git(["git", "log", "--oneline", "HEAD..origin/HEAD"])
    lines = raw.splitlines()
    return "\n".join(f"`{line}`" for line in lines)


# -------------------------------------------------
# Handler
# -------------------------------------------------
async def handler(event, args):
    if not is_owner(event):
        return await respond(event, "You are not allowed to use this command.")

    if config.RUN_MODE == "bot":
        return await respond(event, "Control commands are disabled in BOT mode.")

    if not ensure_git_repo():
        return await respond(
            event,
            "Git repository not found.\n"
            "Atlas must be cloned from GitHub to use update."
        )

    cmd = event.raw_text.split()[0].lstrip("./").lower()
    sub = args[0].lower() if args else None

    chat_id = event.chat_id
    message_id = event.id

    # -------------------------------------------------
    # RESTART
    # -------------------------------------------------
    if cmd == "restart":
        await respond(event, "Restarting Atlas…")

        set_action(
            action="restart",
            chat_id=chat_id,
            message_id=message_id,
        )

        await log_event("Restart Initiated", "Restart requested")
        await asyncio.sleep(1)

        os.execv(sys.executable, [sys.executable] + sys.argv)

    # -------------------------------------------------
    # UPDATE
    # -------------------------------------------------
    if cmd == "update":
        # Step 1: check updates
        if sub != "now":
            await respond(event, "Checking for updates…")

            try:
                local = get_local_commit()
                remote = get_remote_commit()
            except Exception:
                return await respond(
                    event,
                    "Git metadata not available.\n"
                    "If running in Docker, ensure the repository (including .git) "
                    "is bind-mounted correctly."
                )

            if local == remote:
                return await respond(event, "Atlas is already up to date.")

            changelog = get_changelog()
            if not changelog:
                changelog = "`No changelog available.`"

            return await respond(
                event,
                "**Update Available**\n\n"
                "**Changelog**\n"
                f"{changelog}\n\n"
                "Run `.update now` to apply the update."
            )

        # Step 2: apply update
        await respond(event, "Updating Atlas…")

        set_action(
            action="update",
            chat_id=chat_id,
            message_id=message_id,
        )

        await log_event("Update Initiated", "Update requested")

        try:
            run_git(["git", "pull", "--ff-only"])
        except Exception as e:
            return await respond(event, f"Update failed:\n`{e}`")

        await asyncio.sleep(1)
        os.execv(sys.executable, [sys.executable] + sys.argv)
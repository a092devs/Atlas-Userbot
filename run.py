import asyncio
import signal
import time

from telethon.events import NewMessage

from clients import clients
from dispatcher import dispatcher
from loader import loader

from utils.logger import log, clear_logs, setup as setup_logging, log_event
from plugins.utils.forwarder import start_worker, handle_incoming

from db.control import (
    get_pending,
    mark_done,
    clear_all,
    get_log_chat_id,
)

from core.version import get_version
from db import apikeys
from config import config

from plugins.system.afk import AFK, clear_afk


# -------------------------------------------------
# Global start time (used by alive / uptime)
# -------------------------------------------------
START_TIME = time.time()


# -------------------------------------------------
# Reconcile pending restart / update after reboot
# -------------------------------------------------
async def reconcile_control_state() -> bool:
    row = get_pending()
    if not row:
        return False

    client = clients.user
    if not client:
        return False

    try:
        entity = await client.get_input_entity(row["chat_id"])
        await client.edit_message(
            entity,
            row["message_id"],
            f"Update completed successfully",
        )

        log_event(
            event=f"{row['action'].capitalize()} completed",
            details="Operation finished successfully",
        )

        mark_done(row["id"], "success")

    except Exception as e:
        log.error(f"Reconciliation failed: {e}")
        mark_done(row["id"], "failed")

    finally:
        clear_all()

    return True


# -------------------------------------------------
# Main runtime
# -------------------------------------------------
async def main():
    # -------------------------------------------------
    # Restore log group from DB (CRITICAL FIX)
    # -------------------------------------------------
    config.LOG_CHAT_ID = get_log_chat_id()

    # -------------------------------------------------
    # Clear logs and mark fresh startup
    # -------------------------------------------------
    clear_logs()

    log_event(
        event="Logs Cleared",
        details="Fresh startup, restart, or update",
    )

    apikeys.init()
    version, codename = get_version()

    try:
        await clients.start()
    except RuntimeError as e:
        log.error(str(e))
        print("\nRun `python gensession.py` first.\n")
        return

    # Attach Telegram client to logger
    if clients.bot:
        setup_logging(clients.bot)

    # User account needs dialogs for entity resolution
    if clients.user:
        await clients.user.get_dialogs()

    dispatcher.bind(clients.user, clients.bot)

    # -------------------------------------------------
    # Load plugins
    # -------------------------------------------------
    loader.load()

    if clients.user:
        start_worker(clients.user)

        @clients.user.on(NewMessage(incoming=True))
        async def forwarder_incoming_handler(event):
            await handle_incoming(event)

    log.info(f"Atlas runtime initialized — v{version} ({codename})")

    # -------------------------------------------------
    # Reconcile restart/update AFTER everything is ready
    # -------------------------------------------------
    was_controlled = await reconcile_control_state()

    if not was_controlled:
        log_event(
            event="Bot started",
            details=f"Atlas v{version} ({codename}) is up and running",
        )

    # -------------------------------------------------
    # Keep clients alive
    # -------------------------------------------------
    await asyncio.gather(
        *[
            c.run_until_disconnected()
            for c in (clients.user, clients.bot)
            if c
        ]
    )


# -------------------------------------------------
# Graceful shutdown
# -------------------------------------------------
def shutdown():
    log.info("Shutdown signal received")
    for task in asyncio.all_tasks():
        task.cancel()


if __name__ == "__main__":
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: shutdown())

    asyncio.run(main())

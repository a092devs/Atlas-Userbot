import json
import time
import asyncio

from telethon.errors import FloodWaitError

from db.core import db
from utils.respond import respond
from utils.logger import log_event


# -------------------------------------------------
# Runtime state
# -------------------------------------------------
_forward_queue: asyncio.Queue | None = None
_worker_task: asyncio.Task | None = None

_album_buffer = {}
_album_tasks = {}


__plugin__ = {
    "name": "Forwarder",
    "category": "utils",
    "description": "Automatically forward messages between chats",
    "commands": {
        "fw": "Base command for message forwarder",
        "fw add": "Add a new forwarding rule (ID or @username)",
        "fw del": "Delete a forwarding rule",
        "fw list": "List all forwarding rules",
        "fw on": "Enable a forwarding rule",
        "fw off": "Disable a forwarding rule",
    },
}


# -------------------------------------------------
# DB helpers
# -------------------------------------------------
def _rules_index():
    raw = db.get("fw:rules", "")
    return [r for r in raw.split(",") if r]


def _save_rules_index(rules):
    db.set("fw:rules", ",".join(rules))


def _rule_key(rule_id: str) -> str:
    return f"fw:rule:{rule_id}"


def _load_rule(rule_id: str):
    raw = db.get(_rule_key(rule_id))
    return json.loads(raw) if raw else None


def _save_rule(rule_id: str, data: dict):
    db.set(_rule_key(rule_id), json.dumps(data))


def _delete_rule(rule_id: str):
    db.delete(_rule_key(rule_id))


def _new_rule_id():
    return str(int(time.time() * 1000))


# -------------------------------------------------
# Worker lifecycle
# -------------------------------------------------
def start_worker(client):
    global _forward_queue, _worker_task

    if _forward_queue:
        return  # already running

    _forward_queue = asyncio.Queue()
    _worker_task = asyncio.create_task(_forward_worker(client))


# -------------------------------------------------
# Rule helpers
# -------------------------------------------------
def get_active_rules_for_chat(chat_id: int):
    rules = []
    for rid in _rules_index():
        rule = _load_rule(rid)
        if rule and rule.get("enabled") and rule.get("src") == chat_id:
            rules.append(rule)
    return rules


# -------------------------------------------------
# Album handling
# -------------------------------------------------
async def _delayed_album_flush(grouped_id, client, dst, delay):
    await asyncio.sleep(1.2)
    await _flush_album(grouped_id, client, dst, delay)


async def _flush_album(grouped_id, client, dst, delay):
    messages = _album_buffer.pop(grouped_id, [])
    _album_tasks.pop(grouped_id, None)

    if not messages:
        return

    files = []
    caption = None

    for msg in messages:
        if msg.media:
            files.append(msg.media)
            if msg.text and not caption:
                caption = msg.text

    try:
        if files:
            await client.send_file(dst, files, caption=caption)
        elif caption:
            await client.send_message(dst, caption)

        await asyncio.sleep(delay)

    except FloodWaitError as e:
        await asyncio.sleep(e.seconds + 1)

    except Exception:
        pass


# -------------------------------------------------
# Incoming message hook (called from run.py)
# -------------------------------------------------
async def handle_incoming(event):
    message = event.message
    chat_id = event.chat_id

    rules = get_active_rules_for_chat(chat_id)
    if not rules:
        return

    for rule in rules:
        dst = rule["dst"]
        delay = rule.get("delay", 2)

        # Album
        if message.grouped_id:
            gid = message.grouped_id
            _album_buffer.setdefault(gid, []).append(message)

            if gid not in _album_tasks:
                _album_tasks[gid] = asyncio.create_task(
                    _delayed_album_flush(gid, event.client, dst, delay)
                )
            return

        await enqueue(message, dst, delay)


# -------------------------------------------------
# Forward worker (SINGLE definition)
# -------------------------------------------------
async def _forward_worker(client):
    while True:
        message, dst, delay = await _forward_queue.get()

        try:
            # Text
            if not message.media:
                await client.send_message(dst, message.text or "")

            # Media
            else:
                try:
                    await client.send_file(
                        dst,
                        message.media,
                        caption=message.text,
                    )
                except Exception:
                    file = await message.download_media()
                    if file:
                        await client.send_file(dst, file, caption=message.text)

            await asyncio.sleep(delay)

        except FloodWaitError as e:
            await asyncio.sleep(e.seconds + 1)

        except Exception:
            pass


# -------------------------------------------------
# Queue API
# -------------------------------------------------
async def enqueue(message, dst: int, delay: int = 2):
    if not _forward_queue:
        return
    await _forward_queue.put((message, dst, delay))


# -------------------------------------------------
# Utilities
# -------------------------------------------------
async def _resolve_chat(event, value: str) -> int | None:
    try:
        if value.startswith("@"):
            entity = await event.client.get_entity(value)
            return entity.id
        return int(value)
    except Exception:
        return None


# -------------------------------------------------
# Command handler
# -------------------------------------------------
async def handler(event, args):
    if not args:
        return await respond(
            event,
            "🔁 **Forwarder**\n\n"
            "**Commands:**\n"
            "• `fw add <src_id|@src> <dst_id|@dst>`\n"
            "• `fw del <rule_id>`\n"
            "• `fw on <rule_id>`\n"
            "• `fw off <rule_id>`\n"
            "• `fw list`",
        )

    cmd = args[0].lower()

    # ---------------- fw add ----------------
    if cmd == "add":
        if len(args) < 3:
            return await respond(event, "❌ Usage: `fw add <src> <dst>`")

        src = await _resolve_chat(event, args[1])
        dst = await _resolve_chat(event, args[2])

        if not src or not dst:
            return await respond(
                event,
                "❌ Could not resolve source or destination chat.\n"
                "Make sure the username is valid and you have access.",
            )

        rule_id = _new_rule_id()
        rule = {
            "src": src,
            "dst": dst,
            "enabled": True,
            "delay": 2,
        }

        rules = _rules_index()
        rules.append(rule_id)
        _save_rules_index(rules)
        _save_rule(rule_id, rule)

        log_event(
            event="Forwarder",
            details=(
                "Rule added\n"
                f"ID: {rule_id}\n"
                f"From: {src}\n"
                f"To: {dst}"
            ),
        )

        return await respond(
            event,
            "✅ **Forwarding rule added**\n\n"
            f"🆔 **ID:** `{rule_id}`\n"
            f"📥 **From:** `{src}`\n"
            f"📤 **To:** `{dst}`\n"
            "⚙️ **Status:** Enabled",
        )

    # ---------------- fw del ----------------
    if cmd == "del":
        if len(args) < 2:
            return await respond(event, "❌ Usage: `fw del <rule_id>`")

        rule_id = args[1]
        rules = _rules_index()

        if rule_id not in rules:
            return await respond(event, "❌ Rule not found.")

        rules.remove(rule_id)
        _save_rules_index(rules)
        _delete_rule(rule_id)

        log_event("Forwarder", f"Rule deleted\nID: {rule_id}")
        return await respond(event, f"🗑 **Rule `{rule_id}` deleted.**")

    # ---------------- fw on / off ----------------
    if cmd in ("on", "off"):
        if len(args) < 2:
            return await respond(event, f"❌ Usage: `fw {cmd} <rule_id>`")

        rule_id = args[1]
        rule = _load_rule(rule_id)

        if not rule:
            return await respond(event, "❌ Rule not found.")

        rule["enabled"] = cmd == "on"
        _save_rule(rule_id, rule)

        state = "enabled" if cmd == "on" else "disabled"
        return await respond(event, f"⚙️ **Rule `{rule_id}` {state}.**")

    # ---------------- fw list ----------------
    if cmd == "list":
        rules = _rules_index()
        if not rules:
            return await respond(event, "📭 No forwarding rules configured.")

        text = "🔁 **Forwarding Rules**\n\n"

        for rid in rules:
            rule = _load_rule(rid)
            if not rule:
                continue

            status = "🟢 ENABLED" if rule["enabled"] else "🔴 DISABLED"

            text += (
                f"🆔 **ID:** `{rid}`\n"
                f"📥 **From:** `{rule['src']}`\n"
                f"📤 **To:** `{rule['dst']}`\n"
                f"⚙️ **Status:** {status}\n\n"
            )

        return await respond(event, text.strip())

    return await respond(event, "❌ Unknown subcommand. Use `fw`.")

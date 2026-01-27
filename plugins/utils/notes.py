from db.core import db
from utils.respond import respond
from utils.logger import log_event


__plugin__ = {
    "name": "Notes",
    "category": "utils",
    "description": "Save, retrieve, and manage text notes per chat",
    "commands": {
        "note": "Base command for notes",
        "note set": "Save a new note or overwrite an existing one",
        "note get": "Retrieve a saved note by name",
        "note del": "Delete a saved note",
        "note list": "List all saved notes in the current chat",
    },
}


# -------------------------------------------------
# Helpers
# -------------------------------------------------
def _key(chat_id: int, name: str) -> str:
    return f"notes:{chat_id}:{name.lower()}"


# -------------------------------------------------
# Main handler
# -------------------------------------------------
async def handler(event, args):
    if not args:
        return await respond(
            event,
            "📒 **Notes Module**\n\n"
            "**Available commands:**\n"
            "• `note set <name> <text>` — Save a note\n"
            "• `note get <name>` — Get a saved note\n"
            "• `note del <name>` — Delete a note\n"
            "• `note list` — List all notes\n"
        )

    cmd = args[0].lower()
    chat_id = event.chat_id

    # -------------------------------------------------
    # note set <name> <text>
    # -------------------------------------------------
    # -------------------------------------------------
# note set <name> [text]
# -------------------------------------------------
    if cmd == "set":
        if len(args) < 2:
            return await respond(
                event,
                "❌ **Usage:**\n"
                "`note set <name> <text>`\n"
                "or reply to a message with:\n"
                "`note set <name>`",
            )

        name = args[1]

        reply = await event.get_reply_message()
        if reply and reply.text:
            content = reply.text
        elif len(args) > 2:
            content = " ".join(args[2:])
        else:
            return await respond(
                event,
                "❌ No content to save.\n"
                "Provide text or reply to a message.",
            )

        db.set(_key(chat_id, name), content)

        log_event(
            event="NOTE_SET",
            details=f"Saved note '{name}'",
        )

        return await respond(
            event,
            f"📝 **Note saved**\n"
            f"• Name: `{name}`\n"
            f"• Source: {'reply' if reply else 'text'}",
        )


    # -------------------------------------------------
    # note get <name>
    # -------------------------------------------------
    if cmd == "get":
        if len(args) < 2:
            return await respond(
                event,
                "❌ **Usage:** `note get <name>`\n"
                "Retrieve a previously saved note.",
            )

        name = args[1]
        note = db.get(_key(chat_id, name))

        if not note:
            return await respond(event, "❌ Note not found.")

        return await respond(
            event,
            f"🗒 **Note: `{name}`**\n\n{note}",
        )

    # -------------------------------------------------
    # note del <name>
    # -------------------------------------------------
    if cmd == "del":
        if len(args) < 2:
            return await respond(
                event,
                "❌ **Usage:** `note del <name>`\n"
                "Delete a saved note.",
            )

        name = args[1]
        key = _key(chat_id, name)

        if not db.get(key):
            return await respond(event, "❌ Note not found.")

        db.delete(key)

        log_event(
            event="NOTE_DELETE",
            details=f"Deleted note '{name}'",
        )

        return await respond(
            event,
            f"🗑 **Note deleted**\n"
            f"• Name: `{name}`",
        )

    # -------------------------------------------------
    # note list
    # -------------------------------------------------
    if cmd == "list":
        prefix = f"notes:{chat_id}:"
        keys = db.keys(prefix)

        if not keys:
            return await respond(event, "📭 No notes saved in this chat.")

        names = sorted(k.split(":")[-1] for k in keys)
        text = (
            "📒 **Saved Notes**\n\n"
            + "\n".join(f"• `{n}`" for n in names)
        )

        return await respond(event, text)

    # -------------------------------------------------
    # Unknown subcommand
    # -------------------------------------------------
    return await respond(
        event,
        "❌ Unknown subcommand.\n"
        "Use `note` to see available options.",
    )

import json
from datetime import datetime

from utils.respond import respond


__plugin__ = {
    "name": "MsgInfo",
    "category": "utils",
    "description": "Inspect raw Telegram message data",
    "commands": {
        "msginfo": "Show raw message data (reply to a message)",
    },
}


# -------------------------------------------------
# Helpers
# -------------------------------------------------
def _serialize(obj):
    """
    Safely serialize Telethon objects into JSON-friendly data.
    """
    if obj is None:
        return None

    if isinstance(obj, (str, int, float, bool)):
        return obj

    if isinstance(obj, datetime):
        return obj.isoformat()

    if isinstance(obj, list):
        return [_serialize(i) for i in obj]

    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}

    # Telethon objects usually expose to_dict()
    if hasattr(obj, "to_dict"):
        try:
            return _serialize(obj.to_dict())
        except Exception:
            return str(obj)

    return str(obj)


# -------------------------------------------------
# Handler
# -------------------------------------------------
async def handler(event, args):
    reply = await event.get_reply_message()
    if not reply:
        return await respond(
            event,
            "Reply to a message to inspect its raw data."
        )

    try:
        raw = reply.to_dict()
        data = _serialize(raw)
    except Exception as e:
        return await respond(
            event,
            f"Failed to extract message data:\n`{e}`"
        )

    text = json.dumps(
        data,
        indent=2,
        ensure_ascii=False,
    )

    # Telegram message length safety
    if len(text) > 4000:
        file_bytes = text.encode("utf-8")
        return await event.client.send_file(
            event.chat_id,
            file=file_bytes,
            filename="message_raw.json",
            caption="Raw message data",
        )

    return await respond(
        event,
        f"```\n{text}\n```"
    )

import re

from utils.respond import respond


__plugin__ = {
    "name": "SedSubstitution",
    "category": "utils",
    "description": (
        "Advanced sed-style regex substitution.\n\n"
        "Usage:\n"
        "Reply or send:\n"
        "`s/pattern/replacement/`\n"
        "`s/pattern/replacement/g`\n"
        "`s#pattern#replacement#gi`\n\n"
        "Flags:\n"
        "g → global\n"
        "i → ignore case"
    ),
    "commands": {},  # raw trigger
}


async def get_target_message(event):
    reply = await event.get_reply_message()
    if reply and reply.text:
        return reply

    # If not reply, fetch previous message
    async for msg in event.client.iter_messages(
        event.chat_id,
        limit=2
    ):
        if msg.id != event.id and msg.text:
            return msg

    return None


def parse_sed(text):
    if not text.startswith("s"):
        return None

    delimiter = text[1]
    if delimiter.isalnum():
        return None

    parts = text.split(delimiter)

    if len(parts) < 4:
        return None

    pattern = parts[1]
    replacement = parts[2]
    flags = parts[3] if len(parts) > 3 else ""

    return pattern, replacement, flags


async def handler(event, args):
    raw = event.raw_text.strip()

    if not raw.startswith("s"):
        return

    parsed = parse_sed(raw)
    if not parsed:
        return

    pattern, replacement, flags = parsed

    target_msg = await get_target_message(event)
    if not target_msg:
        return

    re_flags = re.MULTILINE

    if "i" in flags:
        re_flags |= re.IGNORECASE

    try:
        if "g" in flags:
            result = re.sub(pattern, replacement, target_msg.text, flags=re_flags)
        else:
            result = re.sub(pattern, replacement, target_msg.text, count=1, flags=re_flags)
    except re.error as e:
        await respond(event, f"Regex error:\n{e}")
        return

    if result == target_msg.text:
        await event.delete()
        return

    await event.delete()
    await respond(event, result)
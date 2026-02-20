import re
from utils.respond import respond


__plugin__ = {
    "name": "SedRaw",
    "category": "utils",
    "description": "Raw sed-style substitution using s/pattern/replacement/flags",
    "commands": {},  # no command needed
}


SED_REGEX = re.compile(r"^s(?P<delim>[^a-zA-Z0-9\s])")


async def get_target_message(event):
    reply = await event.get_reply_message()
    if reply and reply.text:
        return reply

    async for msg in event.client.iter_messages(
        event.chat_id,
        limit=2
    ):
        if msg.id != event.id and msg.text:
            return msg

    return None


def parse_sed(raw):
    match = SED_REGEX.match(raw)
    if not match:
        return None

    delim = match.group("delim")

    parts = raw.split(delim)

    if len(parts) < 4:
        return None

    pattern = parts[1]
    replacement = parts[2]
    flags = parts[3] if len(parts) > 3 else ""

    return pattern, replacement, flags


async def handler(event, args):
    raw = event.raw_text.strip()

    # Only trigger if raw sed syntax
    parsed = parse_sed(raw)
    if not parsed:
        return  # silently ignore

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
    except re.error:
        return  # silently ignore regex errors

    # Delete sed command message
    await event.delete()

    if result == target_msg.text:
        return

    await respond(event, result)
import re
from utils.respond import respond
from dispatcher import dispatcher  # dispatcher is in root


__plugin__ = {
    "name": "SedRaw",
    "category": "utils",
    "description": "Raw sed-style substitution using s/pattern/replacement/flags",
    "commands": {},
}


# Detect: s<delimiter>
SED_REGEX = re.compile(r"^s(?P<delim>[^a-zA-Z0-9\s])")


async def raw_handler(event):
    raw = (event.raw_text or "").strip()

    match = SED_REGEX.match(raw)
    if not match:
        return False  # not handled

    delim = match.group("delim")
    parts = raw.split(delim)

    if len(parts) < 4:
        return False

    pattern = parts[1]
    replacement = parts[2]
    flags = parts[3] if len(parts) > 3 else ""

    # Get target message
    reply = await event.get_reply_message()

    if reply and reply.text:
        target_text = reply.text
    else:
        target_text = None
        async for msg in event.client.iter_messages(
            event.chat_id,
            limit=2
        ):
            if msg.id != event.id and msg.text:
                target_text = msg.text
                break

        if not target_text:
            await event.delete()
            return True

    re_flags = re.MULTILINE
    if "i" in flags:
        re_flags |= re.IGNORECASE

    try:
        if "g" in flags:
            result = re.sub(
                pattern,
                replacement,
                target_text,
                flags=re_flags
            )
        else:
            result = re.sub(
                pattern,
                replacement,
                target_text,
                count=1,
                flags=re_flags
            )
    except re.error:
        await event.delete()
        return True

    await event.delete()

    if result != target_text:
        await respond(event, result)

    return True  # handled


# Register raw handler
dispatcher.register_raw(raw_handler)
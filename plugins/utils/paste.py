import aiohttp


__plugin__ = {
    "name": "Paste",
    "category": "utils",
    "description": "Paste text to pasty.lus.pm",
    "commands": {
        "paste": "Paste replied text to pasty.lus.pm",
    },
}


async def handler(event, args):
    # must be a reply
    reply = await event.get_reply_message()
    if not reply or not reply.raw_text:
        await event.edit("❌ Reply to a text message.")
        return

    text = reply.raw_text

    await event.edit("⏳ Pasting...")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://pasty.lus.pm/api/v1/pastes",
                json={"content": text},
                headers={
                    "User-Agent": "Mozilla/5.0",
                    "Content-Type": "application/json",
                },
            ) as resp:
                # DO NOT assume JSON
                data = await resp.text()
    except Exception:
        await event.edit("❌ Network error.")
        return

    # pasty returns JSON *as text*
    try:
        import json
        data = json.loads(data)
    except Exception:
        await event.edit("❌ Invalid response from paste service.")
        return

    paste_id = data.get("id")
    if not paste_id:
        await event.edit("❌ Paste failed.")
        return

    await event.edit(
        f"✅ **Pasted successfully**\n"
        f"🔗 https://pasty.lus.pm/{paste_id}.txt\n"
        f"📄 https://pasty.lus.pm/{paste_id}/raw",
        link_preview=False,
    )
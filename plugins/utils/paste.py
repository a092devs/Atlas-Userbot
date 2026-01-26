import aiohttp
import os


__plugin__ = {
    "name": "Paste",
    "category": "utils",
    "description": "Paste text to hastebin, pasty or spacebin",
    "commands": {
        "haste": "Paste replied text to hastebin",
        "pasty": "Paste text to pasty.lus.pm",
        "spacebin": "Paste text to spaceb.in",
    },
}


# =====================================================
# Helpers
# =====================================================

async def get_text(event, args):
    reply = await event.get_reply_message()

    if reply:
        text = reply.text or reply.message
        if text:
            return text

        if reply.document:
            path = await reply.download_media()
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    return f.read()
            finally:
                if path and os.path.exists(path):
                    os.remove(path)

        return None

    if args:
        return " ".join(args)

    return None


# =====================================================
# Paste services (Moon logic, Telethon-safe)
# =====================================================

async def paste_haste(text):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://hastebin.com/documents",
            data=text.encode("utf-8"),
        ) as r:
            if r.status != 200:
                return None

            data = await r.json()
            key = data.get("key")
            if not key:
                return None

    return {
        "bin": "Hastebin",
        "url": f"https://hastebin.com/{key}",
        "raw": f"https://hastebin.com/raw/{key}",
    }


async def paste_pasty(text, ext="txt"):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://pasty.lus.pm/api/v1/pastes",
            json={"content": text},
            headers={"User-Agent": "Mozilla/5.0"},
        ) as r:
            raw = await r.text()

            # pasty sometimes returns plain text
            try:
                data = await r.json()
            except Exception:
                return None

            pid = data.get("id")
            if not pid:
                return None

    return {
        "bin": "Pasty",
        "url": f"https://pasty.lus.pm/{pid}.{ext}",
        "raw": f"https://pasty.lus.pm/{pid}/raw",
    }


async def paste_spacebin(text, ext="txt"):
    form = aiohttp.FormData()
    form.add_field("content", text)
    form.add_field("extension", ext)

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://spaceb.in/api/",
            data=form,
        ) as r:
            if r.status != 200:
                return None

            data = await r.json()
            payload = data.get("payload") or {}
            pid = payload.get("id")
            if not pid:
                return None

    return {
        "bin": "Spacebin",
        "url": f"https://spaceb.in/{pid}",
        "raw": f"https://spaceb.in/{pid}/raw",
    }


# =====================================================
# Handler (Atlas style – EDIT messages)
# =====================================================

async def handler(event, args):
    cmd = event.text.split()[0][1:].lower()

    # extension support: .pasty py
    ext = "txt"
    if args and "." in args[0]:
        ext = args[0].split(".", 1)[1]
        args = args[1:]

    text = await get_text(event, args)

    if not text:
        await event.edit("❌ **No text found to paste.**")
        return

    await event.edit("⏳ **Pasting...**")

    if cmd == "haste":
        result = await paste_haste(text)
    elif cmd == "pasty":
        result = await paste_pasty(text, ext)
    elif cmd == "spacebin":
        result = await paste_spacebin(text, ext)
    else:
        result = None

    if not result:
        await event.edit("❌ **Paste failed.**")
        return

    await event.edit(
        f"**Pasted to {result['bin']}**\n"
        f"🔗 {result['url']}\n"
        f"📄 {result['raw']}",
        link_preview=False,
    )
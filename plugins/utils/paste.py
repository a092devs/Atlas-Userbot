import aiohttp
import os
import json


__plugin__ = {
    "name": "Paste",
    "category": "utils",
    "description": "Paste text to pasty, hastebin or spacebin",
    "commands": {
        "paste": "Paste text (reply / args / file) to pasty",
        "haste": "Paste text to hastebin",
        "spacebin": "Paste text to spacebin",
    },
}


# =====================================================
# Text extraction (reply / args / document)
# =====================================================

async def extract_text(event, args):
    reply = await event.get_reply_message()

    # 1️⃣ reply text / caption
    if reply:
        if reply.raw_text:
            return reply.raw_text

        # 2️⃣ document
        if reply.document:
            path = await reply.download_media()
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    return f.read()
            finally:
                if path and os.path.exists(path):
                    os.remove(path)

    # 3️⃣ args
    if args:
        return " ".join(args)

    return None


# =====================================================
# Paste services
# =====================================================

async def paste_pasty(text):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://pasty.lus.pm/api/v1/pastes",
            json={"content": text},
            headers={
                "User-Agent": "Mozilla/5.0",
                "Content-Type": "application/json",
            },
        ) as resp:
            raw = await resp.text()

    try:
        data = json.loads(raw)
    except Exception:
        return None

    pid = data.get("id")
    if not pid:
        return None

    return {
        "bin": "Pasty",
        "url": f"https://pasty.lus.pm/{pid}.txt",
        "raw": f"https://pasty.lus.pm/{pid}/raw",
    }


async def paste_haste(text):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://hastebin.com/documents",
            data=text.encode("utf-8"),
        ) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()

    key = data.get("key")
    if not key:
        return None

    return {
        "bin": "Hastebin",
        "url": f"https://hastebin.com/{key}",
        "raw": f"https://hastebin.com/raw/{key}",
    }


async def paste_spacebin(text):
    form = aiohttp.FormData()
    form.add_field("content", text)

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://spaceb.in/api/",
            data=form,
        ) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()

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
# Handler (Atlas style)
# =====================================================

async def handler(event, args):
    cmd = event.text.split()[0][1:].lower()

    text = await extract_text(event, args)
    if not text:
        await event.edit("❌ **No text found to paste.**")
        return

    await event.edit("⏳ **Pasting...**")

    if cmd == "haste":
        result = await paste_haste(text)

    elif cmd == "spacebin":
        result = await paste_spacebin(text)

    else:  # .paste → pasty (default)
        result = await paste_pasty(text)

    if not result:
        await event.edit("❌ **Paste failed.**")
        return

    await event.edit(
        f"✅ **Pasted to {result['bin']}**\n"
        f"🔗 {result['url']}\n"
        f"📄 {result['raw']}",
        link_preview=False,
    )
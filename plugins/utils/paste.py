import aiohttp
import os
import json


__plugin__ = {
    "name": "Paste",
    "category": "utils",
    "description": "Paste text to pasty.lus.pm",
    "commands": {
        "paste": "Paste text (reply / args / file) to pasty",
    },
}


# =====================================================
# Text extraction (reply / args / document)
# =====================================================

async def extract_text(event, args):
    reply = await event.get_reply_message()

    # 1️⃣ reply text or caption
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
# Pasty service (working baseline)
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
        "url": f"https://pasty.lus.pm/{pid}.txt",
        "raw": f"https://pasty.lus.pm/{pid}/raw",
    }


# =====================================================
# Handler (Atlas style: edit message)
# =====================================================

async def handler(event, args):
    text = await extract_text(event, args)

    if not text:
        await event.edit("❌ **No text found to paste.**")
        return

    await event.edit("⏳ **Pasting to Pasty...**")

    result = await paste_pasty(text)

    if not result:
        await event.edit("❌ **Paste failed.**")
        return

    await event.edit(
        "✅ **Pasted to Pasty**\n"
        f"🔗 {result['url']}\n"
        f"📄 {result['raw']}",
        link_preview=False,
    )
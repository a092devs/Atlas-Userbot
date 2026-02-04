import aiohttp
import os
import json


__plugin__ = {
    "name": "Paste",
    "category": "utils",
    "description": "Paste text to nekobin.com",
    "commands": {
        "paste": "Paste text (reply / args / file) to Nekobin",
    },
}


# =====================================================
# Text extraction (document > text > args)
# =====================================================

async def extract_text(event, args):
    reply = await event.get_reply_message()

    if reply:
        # 1️⃣ DOCUMENT FIRST (any text-based file)
        if reply.document:
            path = await reply.download_media()
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    if content.strip():
                        return content
            finally:
                if path and os.path.exists(path):
                    os.remove(path)

        # 2️⃣ TEXT / CAPTION
        if reply.raw_text:
            return reply.raw_text

    # 3️⃣ ARGS
    if args:
        return " ".join(args)

    return None


# =====================================================
# Nekobin backend
# =====================================================

async def paste_nekobin(text):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://nekobin.com/api/documents",
            json={"content": text},
            headers={
                "User-Agent": "Mozilla/5.0",
                "Content-Type": "application/json",
            },
        ) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()

    key = data.get("result", {}).get("key")
    if not key:
        return None

    return {
        "url": f"https://nekobin.com/{key}",
        "raw": f"https://nekobin.com/raw/{key}",
    }


# =====================================================
# Handler (Atlas style)
# =====================================================

async def handler(event, args):
    text = await extract_text(event, args)

    if not text:
        await event.edit("❌ **No text found to paste.**")
        return

    await event.edit("⏳ **Pasting to Nekobin...**")

    result = await paste_nekobin(text)

    if not result:
        await event.edit("❌ **Paste failed.**")
        return

    await event.edit(
        "✅ **Pasted to Nekobin**\n"
        f"🔗 {result['url']}\n"
        f"📄 {result['raw']}",
        link_preview=False,
    )
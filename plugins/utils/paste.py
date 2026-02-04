import aiohttp
import os


__plugin__ = {
    "name": "Paste",
    "category": "utils",
    "description": "Paste text to dpaste.com",
    "commands": {
        "paste": "Paste text (reply / args / file) to dpaste",
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
# dpaste backend (STABLE)
# =====================================================

async def paste_dpaste(text):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://dpaste.com/api/v2/",
            data={
                "content": text,
                "syntax": "text",
                "expiry_days": 7,
            },
            headers={
                "User-Agent": "Atlas-Userbot",
            },
        ) as resp:
            if resp.status not in (200, 201):
                return None

            url = (await resp.text()).strip()

    if not url.startswith("https://"):
        return None

    return {
        "url": url,
        "raw": f"{url}.txt",
    }


# =====================================================
# Handler (Atlas style)
# =====================================================

async def handler(event, args):
    text = await extract_text(event, args)

    if not text:
        await event.edit("❌ **No text found to paste.**")
        return

    await event.edit("⏳ **Pasting to dpaste...**")

    result = await paste_dpaste(text)

    if not result:
        await event.edit("❌ **Paste failed.**")
        return

    await event.edit(
        "✅ **Pasted to dpaste**\n"
        f"🔗 {result['url']}\n"
        f"📄 {result['raw']}",
        link_preview=False,
    )
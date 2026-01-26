import aiohttp
import os

from utils.logger import log


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
# Text extraction (Telethon-safe)
# =====================================================

async def get_text(event, args):
    reply = await event.get_reply_message()

    if reply:
        # 1️⃣ plain text / caption
        if reply.raw_text:
            log.debug("Paste: using reply.raw_text")
            return reply.raw_text

        # 2️⃣ document
        if reply.document:
            log.debug("Paste: downloading document")
            path = await reply.download_media()
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    return f.read()
            except Exception as e:
                log.exception("Paste: failed reading document")
                return None
            finally:
                if path and os.path.exists(path):
                    os.remove(path)

        return None

    # no reply → args
    if args:
        log.debug("Paste: using command args")
        return " ".join(args)

    return None


# =====================================================
# Paste providers
# =====================================================

async def paste_haste(text):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://hastebin.com/documents",
                data=text.encode("utf-8"),
            ) as r:
                log.debug(f"Hastebin status: {r.status}")
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

    except Exception:
        log.exception("Paste: hastebin failed")
        return None


async def paste_pasty(text, ext="txt"):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://pasty.lus.pm/api/v1/pastes",
                json={"content": text},
                headers={"User-Agent": "Mozilla/5.0"},
            ) as r:
                log.debug(f"Pasty status: {r.status}")
                if r.status != 200:
                    return None

                # pasty is inconsistent
                try:
                    data = await r.json()
                except Exception:
                    raw = await r.text()
                    log.error(f"Pasty invalid JSON: {raw}")
                    return None

                pid = data.get("id")
                if not pid:
                    return None

        return {
            "bin": "Pasty",
            "url": f"https://pasty.lus.pm/{pid}.{ext}",
            "raw": f"https://pasty.lus.pm/{pid}/raw",
        }

    except Exception:
        log.exception("Paste: pasty failed")
        return None


async def paste_spacebin(text, ext="txt"):
    try:
        form = aiohttp.FormData()
        form.add_field("content", text)
        form.add_field("extension", ext)

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://spaceb.in/api/",
                data=form,
            ) as r:
                log.debug(f"Spacebin status: {r.status}")
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

    except Exception:
        log.exception("Paste: spacebin failed")
        return None


# =====================================================
# Handler (Atlas standard: edit message)
# =====================================================

async def handler(event, args):
    cmd = event.text.split()[0][1:].lower()

    # extension support
    ext = "txt"
    if args and "." in args[0]:
        ext = args[0].split(".", 1)[1]
        args = args[1:]

    text = await get_text(event, args)

    if not text:
        log.warning("Paste: no text found")
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
        log.error(f"Paste failed for command: {cmd}")
        await event.edit("❌ **Paste failed. Check logs.**")
        return

    await event.edit(
        f"**Pasted to {result['bin']}**\n"
        f"🔗 {result['url']}\n"
        f"📄 {result['raw']}",
        link_preview=False,
    )
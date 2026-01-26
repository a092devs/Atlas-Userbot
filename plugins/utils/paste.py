import aiohttp
from dataclasses import dataclass
from typing import Optional


# =====================================================
# Models & Errors
# =====================================================

@dataclass
class PasteResult:
    url: str
    raw_url: Optional[str] = None
    provider: str = "unknown"


class PasteError(Exception):
    pass


class PasteFailed(PasteError):
    pass


# =====================================================
# Paste Providers
# =====================================================

async def paste_nekobin(text: str) -> PasteResult:
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://nekobin.com/api/documents",
            json={"content": text},
        ) as resp:
            if resp.status != 200:
                raise PasteFailed("Nekobin upload failed")

            data = await resp.json()
            key = data["result"]["key"]

    return PasteResult(
        url=f"https://nekobin.com/{key}",
        raw_url=f"https://nekobin.com/raw/{key}",
        provider="nekobin",
    )


async def paste_hastebin(text: str) -> PasteResult:
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://hastebin.com/documents",
            data=text.encode(),
        ) as resp:
            if resp.status != 200:
                raise PasteFailed("Hastebin upload failed")

            data = await resp.json()
            key = data["key"]

    return PasteResult(
        url=f"https://hastebin.com/{key}",
        raw_url=f"https://hastebin.com/raw/{key}",
        provider="hastebin",
    )


# =====================================================
# Shared Paste Logic
# =====================================================

async def run_paste(text: str, providers) -> PasteResult:
    if not text.strip():
        raise PasteFailed("Empty text")

    last_error = None
    for name, func in providers:
        try:
            return await func(text)
        except PasteError as e:
            last_error = e

    raise PasteFailed("All paste providers failed") from last_error


# =====================================================
# Atlas Plugin Metadata
# =====================================================

__plugin__ = {
    "name": "Paste",
    "category": "utils",
    "description": "Paste text to Nekobin or Hastebin",
    "commands": {
        "paste": "Paste text (auto provider)",
        "neko": "Paste text to Nekobin",
        "haste": "Paste text to Hastebin",
    },
}


# =====================================================
# Plugin Handler
# =====================================================

async def handler(event, args):
    cmd = event.pattern_match.group(1)

    # get text from args or reply
    text = " ".join(args).strip()
    if not text:
        reply = await event.get_reply_message()
        if reply and reply.text:
            text = reply.text

    if not text:
        await event.reply("❌ Provide text or reply to a message.")
        return

    try:
        if cmd == "neko":
            result = await run_paste(text, [("nekobin", paste_nekobin)])

        elif cmd == "haste":
            result = await run_paste(text, [("hastebin", paste_hastebin)])

        else:  # .paste → fallback
            result = await run_paste(
                text,
                [
                    ("nekobin", paste_nekobin),
                    ("hastebin", paste_hastebin),
                ],
            )

    except PasteError as e:
        await event.reply(f"❌ Paste failed: `{e}`")
        return

    msg = f"🔗 **Paste ({result.provider})**\n{result.url}"
    if result.raw_url:
        msg += f"\n📄 {result.raw_url}"

    await event.reply(msg)

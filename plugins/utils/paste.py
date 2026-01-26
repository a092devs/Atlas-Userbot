import aiohttp


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
# Paste providers (simple functions)
# =====================================================

async def nekobin(text):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://nekobin.com/api/documents",
            json={"content": text},
        ) as r:
            if r.status != 200:
                return None

            data = await r.json()
            key = data.get("result", {}).get("key")
            if not key:
                return None

    return {
        "provider": "nekobin",
        "url": f"https://nekobin.com/{key}",
        "raw": f"https://nekobin.com/raw/{key}",
    }


async def hastebin(text):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://hastebin.com/documents",
            data=text.encode(),
        ) as r:
            if r.status != 200:
                return None

            data = await r.json()
            key = data.get("key")
            if not key:
                return None

    return {
        "provider": "hastebin",
        "url": f"https://hastebin.com/{key}",
        "raw": f"https://hastebin.com/raw/{key}",
    }


# =====================================================
# Atlas plugin handler
# =====================================================

async def handler(event, args):
    # command without prefix (., !)
    cmd = event.text.split()[0][1:].lower()

    # get text from args or reply
    text = " ".join(args).strip()
    if not text:
        reply = await event.get_reply_message()
        if reply and reply.text:
            text = reply.text

    if not text:
        await event.reply("❌ Provide text or reply to a message.")
        return

    result = None

    if cmd == "neko":
        result = await nekobin(text)

    elif cmd == "haste":
        result = await hastebin(text)

    else:  # .paste → auto fallback
        for func in (nekobin, hastebin):
            result = await func(text)
            if result:
                break

    if not result:
        await event.reply("❌ Paste failed.")
        return

    msg = f"🔗 **Paste ({result['provider']})**\n{result['url']}"
    msg += f"\n📄 {result['raw']}"

    await event.reply(msg)
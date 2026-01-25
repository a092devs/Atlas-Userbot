import time
from utils.respond import respond


__plugin__ = {
    "name": "Ping",
    "category": "system",
    "description": "Check bot latency",
    "commands": {
        "ping": "Measure message round-trip latency",
    },
}


async def handler(event, args):
    start = time.time()

    try:
        msg = await event.edit("🏓 Pinging...")
    except Exception:
        msg = await event.reply("🏓 Pinging...")

    latency = int((time.time() - start) * 1000)

    text = (
        "🏓 **Pong!**\n"
        f"⏱ **Latency:** `{latency} ms`"
    )

    try:
        await msg.edit(text)
    except Exception:
        await respond(event, text)

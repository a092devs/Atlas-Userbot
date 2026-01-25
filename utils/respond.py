async def respond(event, text: str):
    """
    Edit for userbot, reply for bot.
    """
    try:
        # userbot can edit anything
        await event.edit(text)
    except Exception:
        # bot fallback
        await event.reply(text)

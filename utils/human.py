async def format_user(event) -> str:
    """
    Return a human-friendly, clickable user name
    WITHOUT link previews.

    Always uses tg://user?id=... to avoid previews.
    """

    try:
        sender = await event.get_sender()
        user_id = sender.id
    except Exception:
        user_id = event.sender_id

    # Build display name
    try:
        name = " ".join(
            part for part in (
                sender.first_name,
                sender.last_name,
            )
            if part
        ).strip()
    except Exception:
        name = ""

    if not name:
        name = "User"

    # tg:// links never generate previews
    return f"[{name}](tg://user?id={user_id})"

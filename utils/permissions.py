from telethon.tl.types import ChannelParticipantsAdmins


async def is_admin(event) -> bool:
    if event.is_private:
        return False

    try:
        async for user in event.client.iter_participants(
            event.chat_id,
            filter=ChannelParticipantsAdmins,
        ):
            if user.id == event.sender_id:
                return True
    except Exception:
        return False

    return False

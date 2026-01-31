from config import config
from db.core import db


__plugin__ = {
    "name": "AssistantPM",
    "category": "system",
    "description": "Forward assistant bot PMs to owner and relay replies",
    "commands": {},
}


# -------------------------------------------------
# Helpers
# -------------------------------------------------
def _enabled() -> bool:
    return config.RUN_MODE in ("bot", "dual")


def _key(msg_id: int) -> str:
    return f"assistant_pm:{msg_id}"


async def _resolve_user_from_reply(event):
    msg = await event.get_reply_message()
    while msg:
        user_id = db.get(_key(msg.id))
        if user_id:
            return int(user_id)
        msg = await msg.get_reply_message()
    return None


# -------------------------------------------------
# Incoming PM → forward to OWNER
# -------------------------------------------------
async def assistant_pm_forward(event, args):
    if not _enabled():
        return

    if not event.is_private:
        return

    if event.sender_id == config.OWNER_ID:
        return

    forwarded = await event.forward_to(config.OWNER_ID)
    db.set(_key(forwarded.id), str(event.sender_id))


# -------------------------------------------------
# OWNER reply → send back to user
# -------------------------------------------------
async def assistant_pm_reply(event, args):
    if not _enabled():
        return

    if event.sender_id != config.OWNER_ID:
        return

    if not event.is_reply:
        return

    user_id = await _resolve_user_from_reply(event)
    if not user_id:
        return

    if event.media:
        await event.client.send_file(
            user_id,
            event.media,
            caption=event.text or None,
        )
    else:
        await event.client.send_message(
            user_id,
            event.text or "",
        )


# Mark handlers for loader discovery
assistant_pm_forward._assistant_pm = True
assistant_pm_reply._assistant_pm = True

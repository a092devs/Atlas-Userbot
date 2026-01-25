from telethon.tl.types import User, Chat, Channel
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.channels import GetFullChannelRequest

from utils.respond import respond


__plugin__ = {
    "name": "WhoIs",
    "category": "utils",
    "description": "Inspect IDs and detailed user/chat information",
    "commands": {
        "id": "Show contextual IDs (chat, message, user)",
        "whois": "Show detailed profile or chat information",
    },
}


# -------------------------------------------------
# Helpers
# -------------------------------------------------
def get_peer_id(entity) -> str:
    if isinstance(entity, User):
        return str(entity.id)
    return f"-100{entity.id}"


def get_client_dc_id(client):
    try:
        return client.session.dc_id
    except Exception:
        return None


def format_status(user: User) -> str:
    if not user.status:
        return "Unknown"
    return type(user.status).__name__.replace("UserStatus", "")


def format_flags(user: User) -> str:
    flags = []
    if user.bot:
        flags.append("bot")
    if user.verified:
        flags.append("verified")
    if user.scam:
        flags.append("scam")
    if user.fake:
        flags.append("fake")
    if user.restricted:
        flags.append("restricted")
    if user.deleted:
        flags.append("deleted")
    return ", ".join(flags) if flags else "none"


# -------------------------------------------------
# Formatters
# -------------------------------------------------
def format_user_whois(user: User, full):
    lines = [
        "User Information",
        "",
        f"ID: `{user.id}`",
    ]

    if user.first_name or user.last_name:
        name = f"{user.first_name or ''} {user.last_name or ''}".strip()
        lines.append(f"Name: {name}")

    if user.username:
        lines.append(f"Username: `@{user.username}`")

    if full.about:
        lines.extend(["", "Bio:", full.about])

    lines.extend(
        [
            "",
            f"Status: `{format_status(user)}`",
            f"Flags: `{format_flags(user)}`",
        ]
    )

    if full.common_chats_count:
        lines.append(f"Mutual Chats: `{full.common_chats_count}`")

    if user.phone:
        lines.append(f"Phone: `{user.phone}`")

    return "\n".join(lines)


def format_chat_whois(chat, full):
    peer_id = get_peer_id(chat)

    if isinstance(chat, Channel):
        ctype = "supergroup" if chat.megagroup else "channel"
    else:
        ctype = "group"

    lines = [
        "Chat Information",
        "",
        f"ID: `{peer_id}`",
    ]

    if getattr(chat, "title", None):
        lines.append(f"Title: {chat.title}")

    if getattr(chat, "username", None):
        lines.append(f"Username: `@{chat.username}`")

    lines.append(f"Type: `{ctype}`")

    if full.participants_count:
        lines.append(f"Members: `{full.participants_count}`")

    if full.about:
        lines.extend(["", "Description:", full.about])

    if chat.verified:
        lines.append("Verified: `yes`")

    if chat.scam:
        lines.append("Scam: `yes`")

    return "\n".join(lines)


# -------------------------------------------------
# Handler
# -------------------------------------------------
async def handler(event, args):
    cmd = event.raw_text.split()[0].lstrip("./").lower()

    # Resolve entity
    reply = await event.get_reply_message()
    if reply and reply.sender:
        entity = reply.sender
    elif args:
        try:
            entity = await event.client.get_entity(args[0])
        except Exception:
            return await respond(event, "Could not resolve entity.")
    else:
        entity = await event.get_chat()

    # -------------------------------------------------
    # id  → contextual inspector (COPY FRIENDLY)
    # -------------------------------------------------
    if cmd == "id":
        chat = await event.get_chat()
        me = await event.client.get_me()

        chat_id = get_peer_id(chat)
        chat_dc_id = None
        message_id = event.id
        my_id = me.id
        my_dc_id = get_client_dc_id(event.client)

        text = (
    		f"Chat ID: `{chat_id}`\n"
    		f"Chat DC ID: `{chat_dc_id}`\n\n"
    		f"Message ID: `{message_id}`\n"
    		f"Your ID: `{my_id}`\n"
    		f"Your DC ID: `{my_dc_id}`"
		)

        return await respond(event, text)

    # -------------------------------------------------
    # whois  → detailed inspection
    # -------------------------------------------------
    if isinstance(entity, User):
        full = await event.client(GetFullUserRequest(entity))
        text = format_user_whois(entity, full.full_user)

        if entity.photo:
            try:
                return await event.client.send_file(
                    event.chat_id,
                    entity.photo,
                    caption=text,
                )
            except Exception:
                pass

        return await respond(event, text)

    # Chat / Channel
    full = await event.client(GetFullChannelRequest(entity))
    text = format_chat_whois(entity, full.full_chat)

    if getattr(entity, "photo", None):
        try:
            return await event.client.send_file(
                event.chat_id,
                entity.photo,
                caption=text,
            )
        except Exception:
            pass

    return await respond(event, text)
from telethon.tl.types import User, Chat, Channel
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.channels import GetFullChannelRequest

from utils.respond import respond


__plugin__ = {
    "name": "WhoIs",
    "category": "utils",
    "description": "Inspect detailed user or chat information",
    "commands": {
        "id": "Show only ID of user or chat",
        "whois": "Show detailed profile information",
    },
}


# -------------------------------------------------
# Helpers
# -------------------------------------------------
def _format_status(user: User) -> str:
    status = user.status
    if not status:
        return "Unknown"

    name = type(status).__name__
    return name.replace("UserStatus", "")


def _format_user_flags(user: User) -> str:
    flags = []

    if user.bot:
        flags.append("🤖 Bot")
    if user.verified:
        flags.append("✅ Verified")
    if user.scam:
        flags.append("⚠️ Scam")
    if user.fake:
        flags.append("❗ Fake")
    if user.restricted:
        flags.append("🚫 Restricted")
    if user.deleted:
        flags.append("🗑 Deleted")

    return " | ".join(flags) if flags else "None"


# -------------------------------------------------
# Formatters
# -------------------------------------------------
def format_id_only(entity):
    return f"🆔 **ID**\n\n`{entity.id}`"


def format_user_full(user: User, full):
    text = "👤 **User Profile**\n\n"
    text += f"• **User ID:** `{user.id}`\n"

    if user.first_name or user.last_name:
        text += f"• **Name:** {(user.first_name or '')} {(user.last_name or '')}\n"

    if user.username:
        text += f"• **Username:** @{user.username}\n"

    if full.about:
        text += f"\n📝 **Bio:**\n{full.about}\n"

    if user.phone:
        text += f"\n📞 **Phone:** `{user.phone}`\n"

    text += f"\n👁 **Status:** `{_format_status(user)}`\n"
    text += f"🚩 **Flags:** {_format_user_flags(user)}\n"

    if full.common_chats_count:
        text += f"🤝 **Mutual Chats:** `{full.common_chats_count}`\n"

    return text


def format_chat_full(chat, full):
    text = "💬 **Chat Information**\n\n"
    text += f"• **Chat ID:** `{chat.id}`\n"

    if getattr(chat, "title", None):
        text += f"• **Title:** {chat.title}\n"

    if getattr(chat, "username", None):
        text += f"• **Username:** @{chat.username}\n"

    if isinstance(chat, Channel):
        ctype = "Channel" if not chat.megagroup else "Supergroup"
    else:
        ctype = "Group"

    text += f"• **Type:** {ctype}\n"

    if chat.verified:
        text += "• **Verified:** Yes\n"

    if chat.scam:
        text += "• **Scam:** Yes\n"

    if full.about:
        text += f"\n📝 **Description:**\n{full.about}\n"

    if full.participants_count:
        text += f"\n👥 **Members:** `{full.participants_count}`\n"

    return text


# -------------------------------------------------
# Handler
# -------------------------------------------------
async def handler(event, args):
    cmd = event.raw_text.split()[0].lstrip("./").lower()

    # Resolve entity
    entity = None
    reply = await event.get_reply_message()

    if reply and reply.sender:
        entity = reply.sender
    elif args:
        try:
            entity = await event.client.get_entity(args[0])
        except Exception:
            return await respond(event, "❌ Could not resolve entity.")
    else:
        entity = await event.get_chat()

    # ---------------- .id ----------------
    if cmd == "id":
        return await respond(event, format_id_only(entity))

    # ---------------- .whois ----------------
    if isinstance(entity, User):
        full = await event.client(GetFullUserRequest(entity))
        text = format_user_full(entity, full.full_user)

        try:
            if entity.photo:
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
    text = format_chat_full(entity, full.full_chat)

    try:
        if getattr(entity, "photo", None):
            return await event.client.send_file(
                event.chat_id,
                entity.photo,
                caption=text,
            )
    except Exception:
        pass

    return await respond(event, text)
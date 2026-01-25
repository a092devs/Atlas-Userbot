from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.types import ChatBannedRights
from telethon.errors import ChatAdminRequiredError

from utils.respond import respond
from utils.permissions import is_admin


__plugin__ = {
    "name": "Admin",
    "category": "admin",
    "description": "Chat administration tools",
    "commands": {
        "ban": "Ban a user from the chat",
        "unban": "Remove ban from a user",
        "kick": "Kick a user from the chat",
        "mute": "Mute a user (cannot send messages)",
        "unmute": "Unmute a user",
        "purge": "Delete messages in bulk by replying to the first message",
        "del": "Delete a single replied message",
    },
}



# -------------------------------------------------
# Rights presets
# -------------------------------------------------
BAN_RIGHTS = ChatBannedRights(until_date=None, view_messages=True)
UNBAN_RIGHTS = ChatBannedRights(until_date=None, view_messages=False)
MUTE_RIGHTS = ChatBannedRights(until_date=None, send_messages=True)
UNMUTE_RIGHTS = ChatBannedRights(until_date=None, send_messages=False)


# -------------------------------------------------
# Main handler
# -------------------------------------------------
async def handler(event, args):
    if not event.is_group:
        return await respond(event, "❌ This command works in groups only.")

    if not await is_admin(event):
        return await respond(event, "❌ You must be an admin to use this command.")

    if not args:
        return await respond(event, "❌ No command provided.")

    cmd = args[0].lower()
    reply = await event.get_reply_message()

    try:
        if cmd == "del":
            if not reply:
                return await respond(event, "❌ Reply to a message to delete it.")
            await event.client.delete_messages(event.chat_id, reply.id)
            return

        if cmd == "purge":
            if not reply:
                return await respond(event, "❌ Reply to a message to start purging.")

            msgs = []
            async for msg in event.client.iter_messages(
                event.chat_id,
                min_id=reply.id,
                max_id=event.id,
            ):
                msgs.append(msg.id)

            if msgs:
                await event.client.delete_messages(event.chat_id, msgs)

            return await respond(event, f"🧹 Purged `{len(msgs)}` messages.")

        if not reply:
            return await respond(event, "❌ Reply to a user to use this command.")

        user_id = reply.sender_id

        if cmd == "ban":
            await event.client(EditBannedRequest(event.chat_id, user_id, BAN_RIGHTS))
            await respond(event, "🔨 User banned.")

        elif cmd == "unban":
            await event.client(EditBannedRequest(event.chat_id, user_id, UNBAN_RIGHTS))
            await respond(event, "♻️ User unbanned.")

        elif cmd == "kick":
            await event.client.kick_participant(event.chat_id, user_id)
            await respond(event, "👢 User kicked.")

        elif cmd == "mute":
            await event.client(EditBannedRequest(event.chat_id, user_id, MUTE_RIGHTS))
            await respond(event, "🔇 User muted.")

        elif cmd == "unmute":
            await event.client(EditBannedRequest(event.chat_id, user_id, UNMUTE_RIGHTS))
            await respond(event, "🔊 User unmuted.")

    except ChatAdminRequiredError:
        await respond(event, "❌ I need admin rights to do that.")

    except Exception as e:
        await respond(event, f"❌ Error: `{e}`")

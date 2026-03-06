import os
from telethon.errors import YouBlockedUserError
from utils.respond import respond

__plugin__ = {
    "name": "Kang",
    "category": "utils",
    "description": (
        "Steal stickers and add them to your sticker packs.\n\n"
        "Usage:\n"
        "` .kang `\n"
        "` .kang <emoji> `\n"
        "` .kang <packname> `\n"
        "` .kang <emoji> <packname> `"
    ),
    "commands": {
        "kang": "Add replied sticker/photo to your sticker pack"
    },
}

DEFAULT_EMOJI = "🙂"


async def handler(event, args):

    reply = await event.get_reply_message()

    if not reply:
        return await respond(event, "Reply to a sticker or image.")

    emoji = DEFAULT_EMOJI
    packname = None

    if args:
        if len(args) == 1:
            if len(args[0]) <= 2:
                emoji = args[0]
            else:
                packname = args[0]

        elif len(args) >= 2:
            emoji = args[0]
            packname = args[1]

    me = await event.client.get_me()
    username = me.username or str(me.id)

    if not packname:
        packname = f"{username}_kang_pack"

    file = await event.client.download_media(reply)

    try:

        async with event.client.conversation("Stickers", timeout=120) as conv:

            await conv.send_message("/addsticker")
            r = await conv.get_response()

            if "choose the sticker set" in r.text.lower():
                await conv.send_message(packname)
                r = await conv.get_response()

                if "send me the sticker" in r.text.lower():
                    await conv.send_file(file)
                    await conv.get_response()

                    await conv.send_message(emoji)
                    await conv.get_response()

                    await conv.send_message("/done")

                    await respond(
                        event,
                        f"Sticker added\nhttps://t.me/addstickers/{packname}"
                    )
                    return

            if "invalid set" in r.text.lower() or "newpack" in r.text.lower():

                await conv.send_message("/newpack")
                await conv.get_response()

                await conv.send_message(packname)
                await conv.get_response()

                await conv.send_file(file)
                await conv.get_response()

                await conv.send_message(emoji)
                await conv.get_response()

                await conv.send_message("/done")

                await respond(
                    event,
                    f"Sticker pack created\nhttps://t.me/addstickers/{packname}"
                )

    except YouBlockedUserError:
        await respond(event, "Unblock @stickers and try again.")

    except Exception as e:
        await respond(event, f"Error: `{e}`")

    finally:
        if file and os.path.exists(file):
            os.remove(file)
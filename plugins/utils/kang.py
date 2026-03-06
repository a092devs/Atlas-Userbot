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
        "` .kang <emoji> `"
    ),
    "commands": {
        "kang": "Add replied sticker to your sticker pack"
    },
}


DEFAULT_EMOJI = "🙂"


async def handler(event, args):

    reply = await event.get_reply_message()

    if not reply or not reply.sticker:
        return await respond(event, "Reply to a sticker.")

    emoji = DEFAULT_EMOJI
    if args:
        emoji = args[0]

    me = await event.client.get_me()
    username = me.username or str(me.id)

    base_pack = f"{username}_kang"
    pack_name = f"{base_pack}_1"

    file = await event.client.download_media(reply.sticker)

    try:

        async with event.client.conversation("Stickers", timeout=120) as conv:

            await conv.send_message("/addsticker")
            r = await conv.get_response()

            if r.buttons:

                found = False

                for row in r.buttons:
                    for button in row:

                        if username in button.text and "kang" in button.text:
                            await conv.send_message(button.text)
                            pack_name = button.text
                            found = True
                            break

                    if found:
                        break

                if not found:

                    await conv.send_message("/newpack")
                    await conv.get_response()

                    await conv.send_message(f"{username}'s Kang Pack")
                    await conv.get_response()

                    await conv.send_file(file)
                    await conv.get_response()

                    await conv.send_message(emoji)
                    await conv.get_response()

                    await conv.send_message("/publish")
                    await conv.get_response()

                    await conv.send_message(pack_name)
                    await conv.get_response()

                    await respond(
                        event,
                        f"Sticker pack created\nhttps://t.me/addstickers/{pack_name}"
                    )

                    return

            await conv.send_file(file)
            await conv.get_response()

            await conv.send_message(emoji)
            await conv.get_response()

            await conv.send_message("/done")

            await respond(
                event,
                f"Sticker added\nhttps://t.me/addstickers/{pack_name}"
            )

    except YouBlockedUserError:
        await respond(event, "Unblock @stickers first.")

    except Exception as e:
        await respond(event, f"Error: `{e}`")

    finally:
        if file and os.path.exists(file):
            os.remove(file)
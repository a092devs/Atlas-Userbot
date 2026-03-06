import os
import re
from PIL import Image

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
        "kang": "Add replied sticker to your pack"
    },
}


DEFAULT_EMOJI = "🙂"


def is_emoji(s):
    return bool(re.match(r"[\U00010000-\U0010ffff]", s))


def convert_to_webp(path):

    img = Image.open(path).convert("RGBA")
    img.thumbnail((512, 512))

    canvas = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    canvas.paste(img, ((512 - img.width)//2, (512 - img.height)//2))

    out = path + ".webp"
    canvas.save(out, "WEBP")

    os.remove(path)
    return out


async def handler(event, args):

    reply = await event.get_reply_message()

    if not reply:
        return await respond(event, "Reply to a sticker or image.")

    emoji = DEFAULT_EMOJI
    packname = None

    if args:

        if len(args) == 1:

            if is_emoji(args[0]):
                emoji = args[0]
            else:
                packname = args[0]

        elif len(args) >= 2:

            emoji = args[0]
            packname = args[1]

    me = await event.client.get_me()
    username = me.username or str(me.id)

    if not packname:
        packname = f"{username}_kang_1"

    file = await event.client.download_media(reply)

    if not file.endswith(".webp"):
        file = convert_to_webp(file)

    try:

        async with event.client.conversation("Stickers", timeout=120) as conv:

            await conv.send_message("/addsticker")
            r = await conv.get_response()

            if "choose the sticker set" in r.text.lower():

                await conv.send_message(packname)
                r = await conv.get_response()

                if "invalid set" in r.text.lower():

                    await conv.send_message("/newpack")
                    await conv.get_response()

                    await conv.send_message(f"{username}'s Kang Pack")
                    await conv.get_response()

                    await conv.send_file(file, force_document=True)
                    await conv.get_response()

                    await conv.send_message(emoji)
                    await conv.get_response()

                    await conv.send_message("/publish")
                    await conv.get_response()

                    await conv.send_message(packname)
                    await conv.get_response()

                    await respond(
                        event,
                        f"Sticker pack created\nhttps://t.me/addstickers/{packname}"
                    )

                    return

            await conv.send_file(file, force_document=True)
            await conv.get_response()

            await conv.send_message(emoji)
            await conv.get_response()

            await conv.send_message("/done")

            await respond(
                event,
                f"Sticker added\nhttps://t.me/addstickers/{packname}"
            )

    except YouBlockedUserError:
        await respond(event, "Unblock @stickers first.")

    except Exception as e:
        await respond(event, f"Error: `{e}`")

    finally:
        if os.path.exists(file):
            os.remove(file)
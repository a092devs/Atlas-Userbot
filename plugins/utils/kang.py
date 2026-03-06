import os
import re
import tempfile
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
        "kang": "Add replied sticker to your pack",
    },
}


DEFAULT_EMOJI = "🙂"


def is_emoji(s: str) -> bool:
    return bool(re.match(r"[\U00010000-\U0010ffff]", s))


def convert_to_webp(path: str) -> str:
    img = Image.open(path).convert("RGBA")
    img.thumbnail((512, 512))

    canvas = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    canvas.paste(img, ((512 - img.width) // 2, (512 - img.height) // 2))

    out = path + ".webp"
    canvas.save(out, "WEBP")

    return out


async def handler(event, args):

    reply = await event.get_reply_message()

    if not reply:
        return await respond(event, "Reply to a sticker or image.")

    emoji = DEFAULT_EMOJI
    pack = None

    if args:

        if len(args) == 1:

            if is_emoji(args[0]):
                emoji = args[0]
            else:
                pack = args[0]

        elif len(args) >= 2:

            emoji = args[0]
            pack = args[1]

    me = await event.client.get_me()
    username = me.username or str(me.id)

    if not pack:
        pack = f"{username}_kang_1"
    else:
        pack = f"{username}_{pack}"

    file_path = None
    sticker_path = None

    try:

        file_path = await event.client.download_media(reply)

        ext = os.path.splitext(file_path)[1].lower()

        if ext in [".tgs", ".webm", ".webp"]:
            sticker_path = file_path
        else:
            sticker_path = convert_to_webp(file_path)

        async with event.client.conversation("Stickers", timeout=120) as conv:

            await conv.send_message("/addsticker")
            r = await conv.get_response()

            await conv.send_message(pack)
            r = await conv.get_response()

            if "invalid" in r.text.lower() or "choose the sticker set" not in r.text.lower():

                await conv.send_message("/newpack")
                await conv.get_response()

                await conv.send_message(f"{username} Kang Pack")
                await conv.get_response()

                await conv.send_file(sticker_path, force_document=True)
                await conv.get_response()

                await conv.send_message(emoji)
                await conv.get_response()

                await conv.send_message("/publish")
                await conv.get_response()

                await conv.send_message(pack)
                await conv.get_response()

                await conv.send_message("/skip")
                await conv.get_response()

            else:

                await conv.send_file(sticker_path, force_document=True)
                await conv.get_response()

                await conv.send_message(emoji)
                await conv.get_response()

                await conv.send_message("/done")
                await conv.get_response()

        await respond(
            event,
            f"Sticker added to [{pack}](https://t.me/addstickers/{pack})"
        )

    except YouBlockedUserError:

        await respond(event, "Unblock @stickers first.")

    except Exception as e:

        await respond(event, f"Error: `{e}`")

    finally:

        for f in [file_path, sticker_path]:
            try:
                if f and os.path.exists(f):
                    os.remove(f)
            except:
                pass
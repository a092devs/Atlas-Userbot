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
        "`.kang`\n"
        "`.kang 😂`\n"
        "`.kang packname`\n"
        "`.kang 😂 packname`"
    ),
    "commands": {
        "kang": "Add replied sticker to your pack"
    },
}


DEFAULT_EMOJI = "🙂"
PACK_LIMIT = 120


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

    base_pack = f"{username}_kang"

    if packname:
        base_pack = f"{username}_{packname}"

    pack_index = 1
    pack_short = f"{base_pack}_{pack_index}"

    file = None
    converted = None

    try:

        file = await event.client.download_media(reply)

        ext = os.path.splitext(file)[1].lower()

        if ext in [".tgs", ".webm", ".webp"]:
            converted = file
        else:
            converted = convert_to_webp(file)

        async with event.client.conversation("Stickers", timeout=120) as conv:

            await conv.send_message("/addsticker")
            r = await conv.get_response()

            # detect pack buttons
            if r.buttons:

                packs = []

                for row in r.buttons:
                    for button in row:
                        if base_pack in button.text:
                            packs.append(button.text)

                if packs:
                    pack_short = packs[-1]

                    await conv.send_message(pack_short)
                    r = await conv.get_response()

                    if "120" in r.text or "full" in r.text.lower():
                        pack_index = len(packs) + 1
                        pack_short = f"{base_pack}_{pack_index}"
                        await conv.send_message("/newpack")
                        await conv.get_response()
                    else:
                        pass

                else:
                    await conv.send_message("/newpack")
                    await conv.get_response()

            else:
                await conv.send_message("/newpack")
                await conv.get_response()

            if "choose a name" in r.text.lower() or "name for your set" in r.text.lower():

                await conv.send_message(f"{username}'s Kang Pack")
                await conv.get_response()

            await conv.send_file(converted, force_document=True)
            await conv.get_response()

            await conv.send_message(emoji)
            await conv.get_response()

            await conv.send_message("/publish")
            await conv.get_response()

            await conv.send_message(pack_short)
            await conv.get_response()

            await conv.send_message("/done")

            await respond(
                event,
                f"Sticker added\nhttps://t.me/addstickers/{pack_short}"
            )

    except YouBlockedUserError:
        await respond(event, "Unblock @stickers first.")

    except Exception as e:
        await respond(event, f"Error: `{e}`")

    finally:

        for f in [file, converted]:
            try:
                if f and os.path.exists(f):
                    os.remove(f)
            except:
                pass
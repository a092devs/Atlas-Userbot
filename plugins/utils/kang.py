import os
import re
import tempfile

from PIL import Image

from telethon.errors import YouBlockedUserError

from utils.respond import respond
from db import db


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
PACK_LIMIT = 120


def is_emoji(s: str):
    return bool(re.match(r"[\U00010000-\U0010ffff]", s))


def convert_to_webp(path):

    img = Image.open(path).convert("RGBA")
    img.thumbnail((512, 512))

    canvas = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    canvas.paste(img, ((512 - img.width) // 2, (512 - img.height) // 2))

    out = path + ".webp"
    canvas.save(out, "WEBP")

    return out


def get_pack(owner, pack_key):

    data = db.get("kang_packs", {}).get(owner, {})

    if pack_key in data:
        return data[pack_key]

    return None


def save_pack(owner, pack_key, pack):

    data = db.get("kang_packs", {})

    if owner not in data:
        data[owner] = {}

    data[owner][pack_key] = pack

    db.set("kang_packs", data)


def increment_count(owner, pack_key):

    data = db.get("kang_packs", {})

    pack = data[owner][pack_key]

    pack["count"] += 1

    db.set("kang_packs", data)


def next_pack(owner, pack_key, username):

    data = db.get("kang_packs", {})

    if owner not in data:
        data[owner] = {}

    index = 1

    if pack_key in data[owner]:
        index = data[owner][pack_key]["index"] + 1

    short = f"{username}_{pack_key}_{index}"

    data[owner][pack_key] = {
        "short": short,
        "count": 0,
        "index": index,
    }

    db.set("kang_packs", data)

    return short


async def handler(event, args):

    reply = await event.get_reply_message()

    if not reply:
        return await respond(event, "Reply to a sticker or image.")

    emoji = DEFAULT_EMOJI
    pack_key = "kang"

    if args:

        if len(args) == 1:

            if is_emoji(args[0]):
                emoji = args[0]
            else:
                pack_key = args[0]

        elif len(args) >= 2:

            emoji = args[0]
            pack_key = args[1]

    me = await event.client.get_me()

    username = me.username or str(me.id)
    owner = str(me.id)

    pack = get_pack(owner, pack_key)

    if pack and pack["count"] >= PACK_LIMIT:
        short = next_pack(owner, pack_key, username)
    elif pack:
        short = pack["short"]
    else:
        short = next_pack(owner, pack_key, username)

    file_path = None
    sticker = None

    try:

        file_path = await event.client.download_media(reply)

        ext = os.path.splitext(file_path)[1].lower()

        if ext in [".tgs", ".webm", ".webp"]:
            sticker = file_path
        else:
            sticker = convert_to_webp(file_path)

        async with event.client.conversation("Stickers", timeout=120) as conv:

            await conv.send_message("/addsticker")
            r = await conv.get_response()

            await conv.send_message(short)
            r = await conv.get_response()

            if "invalid set" in r.text.lower():

                await conv.send_message("/newpack")
                await conv.get_response()

                await conv.send_message(f"{username}'s Kang Pack")
                await conv.get_response()

                await conv.send_file(sticker, force_document=True)
                await conv.get_response()

                await conv.send_message(emoji)
                await conv.get_response()

                await conv.send_message("/publish")
                await conv.get_response()

                await conv.send_message(short)
                await conv.get_response()

                await conv.send_message("/skip")
                await conv.get_response()

            else:

                await conv.send_file(sticker, force_document=True)
                await conv.get_response()

                await conv.send_message(emoji)
                await conv.get_response()

                await conv.send_message("/done")
                await conv.get_response()

        increment_count(owner, pack_key)

        await respond(
            event,
            f"Sticker added to [{short}](https://t.me/addstickers/{short})"
        )

    except YouBlockedUserError:

        await respond(event, "Unblock @stickers first.")

    except Exception as e:

        await respond(event, f"Error: `{e}`")

    finally:

        for f in [file_path, sticker]:
            try:
                if f and os.path.exists(f):
                    os.remove(f)
            except:
                pass
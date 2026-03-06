import os
import json
import re
from PIL import Image

from telethon.errors import YouBlockedUserError

from utils.respond import respond
from db.core import db


__plugin__ = {
    "name": "Kang",
    "category": "utils",
    "description": (
        "Steal stickers and add them to your sticker packs.\n\n"
        "Usage:\n"
        "` .kang `\n"
        "` .kang <emoji>`\n"
        "` .kang <packname>`\n"
        "` .kang <emoji> <packname>`"
    ),
    "commands": {
        "kang": "Add replied sticker to your pack",
    },
}


DEFAULT_EMOJI = "🙂"
PACK_LIMIT = 120
DB_KEY = "kang_packs"


# ---------------------------
# Helpers
# ---------------------------

def is_emoji(s):
    return bool(re.match(r"[\U00010000-\U0010ffff]", s))


def convert_to_webp(path):

    img = Image.open(path).convert("RGBA")
    img.thumbnail((512, 512))

    canvas = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    canvas.paste(img, ((512-img.width)//2, (512-img.height)//2))

    out = path + ".webp"
    canvas.save(out, "WEBP")

    return out


def load_db():

    raw = db.get(DB_KEY)

    if not raw:
        return {}

    try:
        return json.loads(raw)
    except:
        return {}


def save_db(data):

    db.set(DB_KEY, json.dumps(data))


def get_pack(owner, key, username):

    data = load_db()

    if owner not in data:
        data[owner] = {}

    if key not in data[owner]:

        short = f"{username}_{key}_1"

        data[owner][key] = {
            "short": short,
            "count": 0,
            "index": 1
        }

        save_db(data)

    return data[owner][key]


def rotate_pack(owner, key, username):

    data = load_db()
    pack = data[owner][key]

    if pack["count"] >= PACK_LIMIT:

        pack["index"] += 1
        pack["count"] = 0
        pack["short"] = f"{username}_{key}_{pack['index']}"

        save_db(data)

    return pack


def increment(owner, key):

    data = load_db()
    data[owner][key]["count"] += 1
    save_db(data)


# ---------------------------
# Main Handler
# ---------------------------

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

        else:

            emoji = args[0]
            pack_key = args[1]

    me = await event.client.get_me()

    username = me.username or str(me.id)
    owner = str(me.id)

    pack = get_pack(owner, pack_key, username)
    pack = rotate_pack(owner, pack_key, username)

    short = pack["short"]

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

            if "choose" not in r.text.lower():
                raise Exception("Unexpected response from @stickers")

            await conv.send_message(short)

            r = await conv.get_response()

            if "invalid set" in r.text.lower():

                # create new pack

                await conv.send_message("/newpack")
                await conv.get_response()

                await conv.send_message(f"{username}'s Kang Pack")
                r = await conv.get_response()

                if "send me the sticker" not in r.text.lower():
                    raise Exception("Sticker prompt not received")

                await conv.send_file(sticker, force_document=True)

                r = await conv.get_response()

                await conv.send_message(emoji)
                await conv.get_response()

                await conv.send_message("/publish")
                await conv.get_response()

                await conv.send_message(short)
                await conv.get_response()

                await conv.send_message("/skip")
                await conv.get_response()

            else:

                if "send me the sticker" not in r.text.lower():
                    raise Exception("Sticker prompt not received")

                await conv.send_file(sticker, force_document=True)

                r = await conv.get_response()

                await conv.send_message(emoji)
                await conv.get_response()

                await conv.send_message("/done")
                await conv.get_response()

        increment(owner, pack_key)

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
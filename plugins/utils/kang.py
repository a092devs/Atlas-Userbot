import os
import re
import json
import tempfile

from PIL import Image

from telethon.errors import StickersetInvalidError
from telethon.tl.types import (
    InputStickerSetShortName,
    InputStickerSetItem
)

from telethon.tl.functions.stickers import (
    CreateStickerSetRequest,
    AddStickerToSetRequest
)

from telethon.tl.functions.messages import GetStickerSetRequest

from utils.respond import respond
from db.core import db


__plugin__ = {
    "name": "Kang",
    "category": "utils",
    "description": "Steal stickers and add them to your sticker packs.",
    "commands": {
        "kang": "Add replied sticker to your pack"
    },
}


DEFAULT_EMOJI = "🙂"
PACK_LIMIT = 120
DB_KEY = "kang_packs"


# ------------------------------------------------
# Emoji detection
# ------------------------------------------------

def is_emoji(s):
    return bool(re.match(r"[\U00010000-\U0010ffff]", s))


# ------------------------------------------------
# DB helpers
# ------------------------------------------------

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


# ------------------------------------------------
# Image conversion
# ------------------------------------------------

def convert_to_webp(path):

    img = Image.open(path).convert("RGBA")
    img.thumbnail((512, 512))

    canvas = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    canvas.paste(img, ((512-img.width)//2, (512-img.height)//2))

    out = path + ".webp"
    canvas.save(out, "WEBP")

    return out


# ------------------------------------------------
# Main handler
# ------------------------------------------------

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

    tmp_file = None
    sticker_file = None

    try:

        tmp_file = await event.client.download_media(reply)

        ext = os.path.splitext(tmp_file)[1].lower()

        if ext in [".tgs", ".webm", ".webp"]:
            sticker_file = tmp_file
        else:
            sticker_file = convert_to_webp(tmp_file)

        uploaded = await event.client.upload_file(sticker_file)

        sticker_item = InputStickerSetItem(
            document=uploaded,
            emoji=emoji
        )

        try:

            await event.client(
                GetStickerSetRequest(
                    stickerset=InputStickerSetShortName(short),
                    hash=0
                )
            )

            await event.client(
                AddStickerToSetRequest(
                    stickerset=InputStickerSetShortName(short),
                    sticker=sticker_item
                )
            )

        except StickersetInvalidError:

            await event.client(
                CreateStickerSetRequest(
                    user_id=me.id,
                    title=f"{username}'s Kang Pack",
                    short_name=short,
                    stickers=[sticker_item]
                )
            )

        increment(owner, pack_key)

        await respond(
            event,
            f"Sticker added to [{short}](https://t.me/addstickers/{short})"
        )

    except Exception as e:

        await respond(event, f"Error: `{e}`")

    finally:

        for f in [tmp_file, sticker_file]:
            try:
                if f and os.path.exists(f):
                    os.remove(f)
            except:
                pass
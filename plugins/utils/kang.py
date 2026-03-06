import os
import re
import json
from PIL import Image

from telethon.errors import StickersetInvalidError
from telethon.tl.types import InputStickerSetShortName, InputStickerSetItem
from telethon.tl.functions.stickers import CreateStickerSetRequest, AddStickerToSetRequest
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


def is_emoji(s):
    return bool(re.match(r"[\U00010000-\U0010ffff]", s))


def convert_to_webp(path):

    img = Image.open(path)

    if img.mode != "RGBA":
        img = img.convert("RGBA")

    img.thumbnail((512, 512), Image.LANCZOS)

    canvas = Image.new("RGBA", (512, 512), (0, 0, 0, 0))

    x = (512 - img.width) // 2
    y = (512 - img.height) // 2

    canvas.paste(img, (x, y))

    out = path + ".webp"

    canvas.save(out, "WEBP", lossless=True, method=6)

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


async def api_kang(client, me, short, emoji, sticker):

    uploaded = await client.upload_file(sticker)

    item = InputStickerSetItem(
        document=uploaded,
        emoji=emoji
    )

    try:

        await client(
            GetStickerSetRequest(
                stickerset=InputStickerSetShortName(short),
                hash=0
            )
        )

        await client(
            AddStickerToSetRequest(
                stickerset=InputStickerSetShortName(short),
                sticker=item
            )
        )

    except StickersetInvalidError:

        await client(
            CreateStickerSetRequest(
                user_id=me.id,
                title=f"{me.username} Kang Pack",
                short_name=short,
                stickers=[item]
            )
        )


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

    tmp = None
    sticker = None

    try:

        tmp = await event.client.download_media(reply)

        ext = os.path.splitext(tmp)[1].lower()

        if ext == ".webp":

            sticker = tmp
            await api_kang(event.client, me, short, emoji, sticker)

        elif ext in [".tgs", ".webm"]:

            async with event.client.conversation("Stickers", timeout=120) as conv:

                await conv.send_message("/addsticker")
                await conv.get_response()

                await conv.send_message(short)
                r = await conv.get_response()

                if "invalid" in r.text.lower():

                    await conv.send_message("/newpack")
                    await conv.get_response()

                    await conv.send_message(f"{username} Kang Pack")
                    await conv.get_response()

                    await conv.send_file(tmp, force_document=True)
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

                    await conv.send_file(tmp, force_document=True)
                    await conv.get_response()

                    await conv.send_message(emoji)
                    await conv.get_response()

                    await conv.send_message("/done")
                    await conv.get_response()

        else:

            sticker = convert_to_webp(tmp)
            await api_kang(event.client, me, short, emoji, sticker)

        increment(owner, pack_key)

        await respond(
            event,
            f"Sticker added to [{short}](https://t.me/addstickers/{short})"
        )

    except Exception as e:

        await respond(event, f"Error: `{e}`")

    finally:

        for f in [tmp, sticker]:
            try:
                if f and os.path.exists(f):
                    os.remove(f)
            except:
                pass
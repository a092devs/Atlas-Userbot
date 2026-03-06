import os
import PIL.Image as Image

from telethon.tl.functions.messages import GetStickerSetRequest
from telethon.tl.functions.stickers import CreateStickerSetRequest, AddStickerToSetRequest
from telethon.tl.types import InputStickerSetShortName, InputStickerSetItem

from utils.respond import respond


__plugin__ = {
    "name": "Kang",
    "category": "utils",
    "description": (
        "Steal stickers or convert images into stickers.\n\n"
        "Usage:\n"
        "` .kang `\n"
        "` .kang <emoji> `\n"
        "` .kang <packname> `\n"
        "` .kang <emoji> <packname> `\n"
        "` .kangp <pack_number> `"
    ),
    "commands": {
        "kang": "Add sticker/image to your pack",
        "kangp": "Add sticker to specific pack number",
    },
}


DEFAULT_EMOJI = "🙂"
PACK_LIMIT = 120


def convert_photo(path):
    img = Image.open(path).convert("RGBA")
    img.thumbnail((512, 512))

    canvas = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    x = (512 - img.width) // 2
    y = (512 - img.height) // 2
    canvas.paste(img, (x, y))

    out = path + ".webp"
    canvas.save(out, "WEBP")

    os.remove(path)
    return out


async def handler(event, args):

    cmd = event.raw_text.split()[0].lstrip("./")
    reply = await event.get_reply_message()

    if not reply:
        return await respond(event, "Reply to a sticker or image.")

    emoji = DEFAULT_EMOJI
    custom_pack = None
    forced_pack = None

    if cmd == "kangp":
        if not args:
            return await respond(event, "Usage: `.kangp <pack_number>`")
        forced_pack = int(args[0])

    else:
        if args:
            if len(args) == 1:
                if len(args[0]) <= 2:
                    emoji = args[0]
                else:
                    custom_pack = args[0]

            elif len(args) >= 2:
                emoji = args[0]
                custom_pack = args[1]

    me = await event.client.get_me()
    username = me.username or str(me.id)

    base_pack = f"{username}_kang_pack"

    if custom_pack:
        base_pack = f"{username}_{custom_pack}"

    pack_name = base_pack if not forced_pack else f"{base_pack}_{forced_pack}"

    if not forced_pack:

        index = 1

        while True:
            try:
                stickerset = await event.client(
                    GetStickerSetRequest(
                        stickerset=InputStickerSetShortName(pack_name),
                        hash=0
                    )
                )

                if len(stickerset.documents) >= PACK_LIMIT:
                    index += 1
                    pack_name = f"{base_pack}_{index}"
                    continue

                break

            except Exception:
                break

    file_path = await event.client.download_media(reply)

    if reply.photo:
        file_path = convert_photo(file_path)

    uploaded = await event.client.upload_file(file_path)

    if os.path.exists(file_path):
        os.remove(file_path)

    try:

        await event.client(
            GetStickerSetRequest(
                stickerset=InputStickerSetShortName(pack_name),
                hash=0
            )
        )

        await event.client(
            AddStickerToSetRequest(
                stickerset=InputStickerSetShortName(pack_name),
                sticker=InputStickerSetItem(
                    document=uploaded,
                    emoji=emoji
                )
            )
        )

        await respond(event, f"Sticker added\nhttps://t.me/addstickers/{pack_name}")

    except Exception:

        await event.client(
            CreateStickerSetRequest(
                user_id=me.id,
                title=f"{username}'s Kang Pack",
                short_name=pack_name,
                stickers=[
                    InputStickerSetItem(
                        document=uploaded,
                        emoji=emoji
                    )
                ]
            )
        )

        await respond(event, f"Sticker pack created\nhttps://t.me/addstickers/{pack_name}")
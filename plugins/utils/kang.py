from telethon.tl.functions.messages import GetStickerSetRequest
from telethon.tl.functions.stickers import CreateStickerSetRequest, AddStickerToSetRequest
from telethon.tl.types import InputStickerSetShortName, InputStickerSetItem

from utils.respond import respond


__plugin__ = {
    "name": "Kang",
    "category": "utils",
    "description": (
        "Steal stickers and add them to your sticker pack.\n\n"
        "Usage:\n"
        "` .kang `\n"
        "` .kang <emoji> `\n"
        "` .kang <packname> `\n"
        "` .kang <emoji> <packname> `"
    ),
    "commands": {
        "kang": "Add a replied sticker to your pack",
    },
}


DEFAULT_EMOJI = "🙂"


async def handler(event, args):

    reply = await event.get_reply_message()

    if not reply or not reply.sticker:
        return await respond(event, "Reply to a sticker to kang it.")

    emoji = DEFAULT_EMOJI
    pack = None

    if args:
        if len(args) == 1:
            if len(args[0]) <= 2:
                emoji = args[0]
            else:
                pack = args[0]

        elif len(args) >= 2:
            emoji = args[0]
            pack = args[1]

    me = await event.client.get_me()
    username = me.username or str(me.id)

    pack_name = f"{username}_kang_pack"

    if pack:
        pack_name = f"{username}_{pack}"

    sticker_document = reply.document

    try:
        await event.client(
            GetStickerSetRequest(
                stickerset=InputStickerSetShortName(pack_name),
                hash=0
            )
        )

    except Exception:

        await event.client(
            CreateStickerSetRequest(
                user_id=me.id,
                title=f"{username}'s Kang Pack",
                short_name=pack_name,
                stickers=[
                    InputStickerSetItem(
                        document=sticker_document,
                        emoji=emoji
                    )
                ]
            )
        )

        return await respond(event, "Sticker pack created and sticker added.")

    try:

        await event.client(
            AddStickerToSetRequest(
                stickerset=InputStickerSetShortName(pack_name),
                sticker=InputStickerSetItem(
                    document=sticker_document,
                    emoji=emoji
                )
            )
        )

        await respond(event, "Sticker added to pack.")

    except Exception as e:
        await respond(event, f"Error: `{e}`")
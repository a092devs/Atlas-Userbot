import os
import aiohttp
from urllib.parse import urlparse

from utils.respond import respond


__plugin__ = {
    "name": "LogToTxt",
    "category": "utils",
    "description": "Convert replied .log file or direct link to .txt",
    "commands": {
        "l2t": "Convert replied .log file or link to .txt",
        "logtotxt": "Convert replied .log file or link to .txt",
    },
}


async def handler(event, args):
    reply = await event.get_reply_message()

    if not reply:
        return await respond(event, "Reply to a **.log file** or a **direct .log link**.")

    await respond(event, "`Processing...`")

    file_path = None

    try:
        # Case 1: Telegram file
        if reply.document:
            filename = reply.file.name or "file.log"

            if not filename.endswith(".log"):
                return await respond(event, "Replied file must be a **.log** file.")

            file_path = await reply.download_media()

        # Case 2: Direct link
        elif reply.text and reply.text.strip().startswith("http"):
            url = reply.text.strip()

            parsed = urlparse(url)
            filename = os.path.basename(parsed.path)

            if not filename.endswith(".log"):
                return await respond(event, "Link must end with **.log**")

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        return await respond(event, "Failed to download the .log file.")

                    content = await resp.read()

            file_path = filename
            with open(file_path, "wb") as f:
                f.write(content)

        else:
            return await respond(event, "Invalid reply. Provide a .log file or direct link.")

        # Convert extension only (no content modification needed)
        new_name = os.path.splitext(file_path)[0] + ".txt"
        os.rename(file_path, new_name)

        await event.client.send_file(
            event.chat_id,
            new_name,
            caption="Converted to .txt"
        )

        os.remove(new_name)
        await event.delete()

    except Exception as e:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        return await respond(event, f"Error:\n{e}")

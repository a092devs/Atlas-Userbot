import os
import requests

from utils.respond import respond


__plugin__ = {
    "name": "Pixeldrain",
    "category": "utils",
    "description": "Upload files to Pixeldrain without API key",
    "commands": {
        "pixeldrain": "Upload replied media or local file to Pixeldrain",
    },
}


UPLOAD_URL = "https://pixeldrain.com/api/file"


def _bytes_to_human(n):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.2f}{unit}"
        n /= 1024
    return f"{n:.2f}PB"


async def handler(event, args):
    reply = await event.get_reply_message()
    local_path = None

    # -------------------------------------------------
    # Resolve file source
    # -------------------------------------------------
    if args:
        local_path = args[0]
        if not os.path.exists(local_path):
            return await respond(event, f"File not found:\n`{local_path}`")
        if not os.path.isfile(local_path):
            return await respond(event, "Provided path is not a file.")

    elif reply and reply.media:
        await respond(event, "Downloading media…")
        try:
            local_path = await reply.download_media()
        except Exception as e:
            return await respond(event, f"Download failed:\n`{e}`")

    else:
        return await respond(
            event,
            "Reply to a media message or provide a local file path."
        )

    if not local_path or not os.path.exists(local_path):
        return await respond(event, "Failed to resolve file.")

    size = os.path.getsize(local_path)

    # -------------------------------------------------
    # Upload to Pixeldrain
    # -------------------------------------------------
    await respond(event, "Uploading to Pixeldrain…")

    try:
        with open(local_path, "rb") as f:
            r = requests.post(
                UPLOAD_URL,
                files={"file": f},
                timeout=600,
            )

        r.raise_for_status()
        data = r.json()

        file_id = data.get("id")
        if not file_id:
            raise RuntimeError("Invalid Pixeldrain response")

        link = f"https://pixeldrain.com/u/{file_id}"

    except Exception as e:
        return await respond(event, f"Pixeldrain upload failed:\n`{e}`")

    text = (
        "Pixeldrain Upload Complete\n\n"
        f"File: `{os.path.basename(local_path)}`\n"
        f"Size: `{_bytes_to_human(size)}`\n"
        f"Link: `{link}`"
    )

    await respond(event, text)

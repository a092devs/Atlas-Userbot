import os
import requests
import re

from utils.respond import respond
from db import apikeys


__plugin__ = {
    "name": "Pixeldrain",
    "category": "utils",
    "description": "Upload and manage files on Pixeldrain",
    "commands": {
        "pixeldrain": "Upload, inspect or delete Pixeldrain files",
    },
}


UPLOAD_URL = "https://pixeldrain.com/api/file"
INFO_URL = "https://pixeldrain.com/api/file/{id}/info"
DELETE_URL = "https://pixeldrain.com/api/file/{id}"


# -------------------------------------------------
# Helpers
# -------------------------------------------------
def _bytes_to_human(n):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.2f}{unit}"
        n /= 1024
    return f"{n:.2f}PB"


def _extract_id(value: str) -> str | None:
    """
    Accept raw ID or Pixeldrain URL.
    """
    m = re.search(r"pixeldrain\.com/(u|api/file)/([a-zA-Z0-9]+)", value)
    if m:
        return m.group(2)
    if re.fullmatch(r"[a-zA-Z0-9]+", value):
        return value
    return None


def _auth_headers():
    key = apikeys.get_key("PIXELDRAIN_API_KEY")
    if not key:
        return None
    return {"Authorization": f"Bearer {key}"}


# -------------------------------------------------
# Upload
# -------------------------------------------------
async def _handle_upload(event, args):
    reply = await event.get_reply_message()
    keep = "--keep" in args
    args = [a for a in args if a != "--keep"]

    local_path = None

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

    size = os.path.getsize(local_path)

    await respond(event, "Uploading to Pixeldrain…")

    try:
        with open(local_path, "rb") as f:
            r = requests.post(
                UPLOAD_URL,
                files={"file": f},
                headers=_auth_headers() or {},
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

    finally:
        if reply and reply.media and not keep:
            try:
                os.remove(local_path)
            except Exception:
                pass

    text = (
        "Pixeldrain Upload Complete\n\n"
        f"File: `{os.path.basename(local_path)}`\n"
        f"Size: `{_bytes_to_human(size)}`\n"
        f"ID: `{file_id}`\n"
        f"Link: `{link}`"
    )

    await respond(event, text)


# -------------------------------------------------
# Info
# -------------------------------------------------
async def _handle_info(event, args):
    if not args:
        return await respond(
            event,
            "Usage:\n"
            "`.pixeldrain info <file_id or link>`"
        )

    file_id = _extract_id(args[0])
    if not file_id:
        return await respond(event, "Invalid Pixeldrain ID or link.")

    try:
        r = requests.get(INFO_URL.format(id=file_id), timeout=30)
        r.raise_for_status()
        data = r.json()

        if data.get("success") is False:
            raise RuntimeError(data)

    except Exception as e:
        return await respond(event, f"Failed to fetch info:\n`{e}`")

    text = (
        "Pixeldrain File Info\n\n"
        f"ID: `{file_id}`\n"
        f"Name: `{data.get('name')}`\n"
        f"Size: `{_bytes_to_human(data.get('size', 0))}`\n"
        f"Mime: `{data.get('mime_type')}`\n"
        f"Views: `{data.get('views')}`\n"
        f"Downloads: `{data.get('downloads')}`\n"
        f"Created: `{data.get('date_upload')}`"
    )

    await respond(event, text)


# -------------------------------------------------
# Delete (requires auth)
# -------------------------------------------------
async def _handle_delete(event, args):
    if not args:
        return await respond(
            event,
            "Usage:\n"
            "`.pixeldrain delete <file_id or link>`"
        )

    headers = _auth_headers()
    if not headers:
        return await respond(
            event,
            "Deletion requires authentication.\n"
            "Set API key using:\n"
            "`.setapi PIXELDRAIN_API_KEY <key>`"
        )

    file_id = _extract_id(args[0])
    if not file_id:
        return await respond(event, "Invalid Pixeldrain ID or link.")

    try:
        r = requests.delete(
            DELETE_URL.format(id=file_id),
            headers=headers,
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()

        if data.get("success") is False:
            raise RuntimeError(data)

    except Exception as e:
        return await respond(event, f"Deletion failed:\n`{e}`")

    await respond(event, f"Pixeldrain file `{file_id}` deleted successfully.")


# -------------------------------------------------
# Main handler
# -------------------------------------------------
async def handler(event, args):
    if not args:
        return await _handle_upload(event, [])

    sub = args[0].lower()

    if sub == "info":
        return await _handle_info(event, args[1:])

    if sub == "delete":
        return await _handle_delete(event, args[1:])

    return await _handle_upload(event, args)
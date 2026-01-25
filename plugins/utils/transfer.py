import os
import shutil
import tempfile
import urllib.request

from utils.respond import respond


__plugin__ = {
    "name": "Transfer",
    "category": "utils",
    "description": "Download and upload files between Telegram, server, and URLs",
    "commands": {
        "dl": "Download replied Telegram media to server",
        "ul": "Upload a file from server to Telegram",
        "fetch": "Download file from URL and upload to Telegram",
    },
}


BASE_DIR = "downloads"


def _bytes_to_human(n):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.2f}{unit}"
        n /= 1024
    return f"{n:.2f}PB"


# -------------------------------------------------
# .dl — Telegram → Server
# -------------------------------------------------
async def _handle_dl(event):
    reply = await event.get_reply_message()
    if not reply or not reply.media:
        return await respond(
            event,
            "Reply to a message containing media to download."
        )

    os.makedirs(BASE_DIR, exist_ok=True)
    await respond(event, "Downloading…")

    try:
        path = await reply.download_media(file=BASE_DIR)
    except Exception as e:
        return await respond(event, f"Download failed:\n`{e}`")

    if not path or not os.path.exists(path):
        return await respond(event, "Download failed.")

    size = os.path.getsize(path)

    return await respond(
        event,
        "Download completed\n\n"
        f"Path: `{path}`\n"
        f"Size: `{_bytes_to_human(size)}`"
    )


# -------------------------------------------------
# .ul — Server → Telegram
# -------------------------------------------------
async def _handle_ul(event, args):
    if not args:
        return await respond(
            event,
            "Usage:\n"
            "`.ul <file_path> [caption]`"
        )

    path = args[0]
    caption = " ".join(args[1:]) if len(args) > 1 else None

    if not os.path.exists(path):
        return await respond(event, f"File not found:\n`{path}`")

    if not os.path.isfile(path):
        return await respond(event, "Provided path is not a file.")

    await respond(event, "Uploading…")

    try:
        await event.client.send_file(
            event.chat_id,
            file=path,
            caption=caption,
        )
    except Exception as e:
        return await respond(event, f"Upload failed:\n`{e}`")


# -------------------------------------------------
# .fetch — URL → Telegram
# -------------------------------------------------
async def _handle_fetch(event, args):
    if not args:
        return await respond(
            event,
            "Usage:\n"
            "`.fetch <direct_url> [caption]`"
        )

    url = args[0]
    caption = " ".join(args[1:]) if len(args) > 1 else None

    await respond(event, "Fetching file…")

    tmp_dir = tempfile.mkdtemp(prefix="atlas_fetch_")
    tmp_path = None

    try:
        filename = os.path.basename(url.split("?")[0]) or "downloaded_file"
        tmp_path = os.path.join(tmp_dir, filename)

        urllib.request.urlretrieve(url, tmp_path)

        if not os.path.exists(tmp_path):
            return await respond(event, "Failed to download file.")

        await event.client.send_file(
            event.chat_id,
            file=tmp_path,
            caption=caption,
        )

    except Exception as e:
        return await respond(event, f"Fetch failed:\n`{e}`")

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


# -------------------------------------------------
# Main handler
# -------------------------------------------------
async def handler(event, args):
    cmd = event.raw_text.split()[0].lstrip("./").lower()

    if cmd == "dl":
        return await _handle_dl(event)

    if cmd == "ul":
        return await _handle_ul(event, args)

    if cmd == "fetch":
        return await _handle_fetch(event, args)

    await respond(event, "Unknown transfer command.")

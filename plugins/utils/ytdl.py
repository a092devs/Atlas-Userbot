import os
from urllib.parse import urlparse, parse_qs

import aiohttp
from yt_dlp import YoutubeDL

from utils.respond import respond
from utils.logger import log_event


__plugin__ = {
    "name": "YTDL",
    "category": "utils",
    "description": "Download videos or audio from YouTube",
    "commands": {
        "ytv": "Download YouTube video",
        "yta": "Download YouTube audio",
    },
}

DOWNLOAD_DIR = "downloads"
THUMB_PATH = "downloads/thumb.jpg"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# -------------------------------------------------
# GLOBAL DOWNLOAD LOCK (single instance)
# -------------------------------------------------
_DOWNLOAD_RUNNING = False


# -------------------------------------------------
# yt-dlp silent logger
# -------------------------------------------------

class DummyLogger:
    def debug(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): pass


# -------------------------------------------------
# Helpers
# -------------------------------------------------

def extract_video_id(url):
    parsed = urlparse(url)
    if parsed.hostname == "youtu.be":
        return parsed.path.lstrip("/")
    if parsed.hostname and "youtube" in parsed.hostname:
        return parse_qs(parsed.query).get("v", [None])[0]
    return None


def ydl_opts(audio: bool):
    opts = {
        "outtmpl": f"{DOWNLOAD_DIR}/%(title)s.%(ext)s",
        "noplaylist": True,
        "default_search": "ytsearch1",

        # silence yt-dlp completely
        "quiet": True,
        "no_warnings": True,
        "logger": DummyLogger(),

        # JS runtime / solver
        "js_runtimes": {"node": {}, "deno": {}},
        "remote_components": ["ejs:github"],
    }

    if audio:
        opts.update(
            {
                "format": "bestaudio/best",
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "0",
                    }
                ],
            }
        )
    else:
        opts["format"] = "bv*+ba/b"

    return opts


async def fetch_thumb(url):
    if not url:
        return None
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                with open(THUMB_PATH, "wb") as f:
                    f.write(await resp.read())
                return THUMB_PATH
    return None


# -------------------------------------------------
# Main handler
# -------------------------------------------------

async def handler(event, args):
    global _DOWNLOAD_RUNNING

    if not args:
        return await respond(
            event,
            "Usage:\n"
            "ytv <url | name>\n"
            "yta <url | name>",
        )

    # ---------------- single-instance guard ----------------
    if _DOWNLOAD_RUNNING:
        return await respond(
            event,
            "Another download is already in progress.\n"
            "Please wait for it to finish.",
        )

    _DOWNLOAD_RUNNING = True
    msg = None

    try:
        cmd = event.raw_text.lstrip("./").split()[0].lower()
        audio = cmd == "yta"
        query = " ".join(args)

        msg = await respond(event, "Starting download")

        with YoutubeDL(ydl_opts(audio)) as ydl:
            info = ydl.extract_info(query, download=False)

            title = info.get("title", "Unknown")
            thumb = await fetch_thumb(info.get("thumbnail"))

            ydl.download([info["webpage_url"]])

        # pick latest downloaded file
        path = max(
            (os.path.join(DOWNLOAD_DIR, f) for f in os.listdir(DOWNLOAD_DIR)),
            key=os.path.getmtime,
        )

        if msg:
            await event.client.edit_message(event.chat_id, msg.id, "Uploading")

        await event.client.send_file(
            event.chat_id,
            path,
            caption=title,
            thumb=thumb,
        )

        # cleanup
        os.remove(path)
        if thumb and os.path.exists(thumb):
            os.remove(thumb)

        log_event("YTDL", "audio" if audio else "video")

        if msg:
            await event.client.delete_messages(event.chat_id, msg.id)

    except Exception as e:
        if msg:
            await event.client.edit_message(
                event.chat_id,
                msg.id,
                f"Download failed: {e}",
            )

    finally:
        # 🔓 ALWAYS release lock
        _DOWNLOAD_RUNNING = False

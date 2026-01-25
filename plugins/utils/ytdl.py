import asyncio
import os
import tempfile
import uuid

from utils.respond import respond
from log.logger import log_event


__plugin__ = {
    "name": "YTDL",
    "category": "utils",
    "description": "Download videos or audio from YouTube and other sites",
    "commands": {
        "ytdl": "Download video from a URL",
        "ytdl audio": "Download audio only (mp3)",
    },
}


# -------------------------------------------------
# Helpers
# -------------------------------------------------
def _build_cmd(url: str, audio: bool, outdir: str):
    base = [
        "yt-dlp",
        "-o", f"{outdir}/%(title)s.%(ext)s",
        "--no-playlist",
        "--restrict-filenames",
    ]

    if audio:
        base += [
            "-x",
            "--audio-format", "mp3",
            "--audio-quality", "0",
        ]

    base.append(url)
    return base


async def _run_cmd(cmd: list[str]):
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    return proc.returncode, stdout.decode(), stderr.decode()


# -------------------------------------------------
# Main handler
# -------------------------------------------------
async def handler(event, args):
    if not args:
        return await respond(
            event,
            "🎬 **YTDL**\n\n"
            "**Usage:**\n"
            "• `ytdl <url>` — download video\n"
            "• `ytdl audio <url>` — download audio (mp3)",
        )

    audio = False
    url = None

    if args[0].lower() == "audio":
        if len(args) < 2:
            return await respond(event, "❌ Usage: `ytdl audio <url>`")
        audio = True
        url = args[1]
    else:
        url = args[0]

    await respond(event, "⏬ **Downloading...**")

    # temp directory per request
    with tempfile.TemporaryDirectory(
        prefix=f"ytdl_{uuid.uuid4().hex}_"
    ) as tmpdir:

        cmd = _build_cmd(url, audio, tmpdir)
        code, out, err = await _run_cmd(cmd)

        if code != 0:
            return await respond(
                event,
                "❌ **Download failed**\n\n"
                f"`{err.strip() or out.strip()}`",
            )

        files = os.listdir(tmpdir)
        if not files:
            return await respond(event, "❌ Download produced no files.")

        path = os.path.join(tmpdir, files[0])

        try:
            await event.client.send_file(
                event.chat_id,
                path,
                caption="🎵 **Audio downloaded**" if audio else "🎥 **Video downloaded**",
            )

            await log_event(
                event="YTDL",
                details=(
                    "Audio download" if audio else "Video download"
                ),
            )

        except Exception as e:
            await respond(event, f"❌ Failed to send file: `{e}`")

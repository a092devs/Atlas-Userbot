import re
import json
import urllib.parse
from random import choice
from subprocess import PIPE, Popen

import requests
from bs4 import BeautifulSoup
from humanize import naturalsize

from utils.respond import respond


__plugin__ = {
    "name": "Direct",
    "category": "utils",
    "description": "Generate direct download links from supported file hosts",
    "commands": {
        "direct": "Generate direct download links from supported URLs",
    },
}


# -------------------------------------------------
# Helpers
# -------------------------------------------------
def subprocess_run(cmd: str):
    cmd_args = cmd.split()
    subproc = Popen(
        cmd_args,
        stdout=PIPE,
        stderr=PIPE,
        universal_newlines=True,
        executable="bash",
    )
    stdout, stderr = subproc.communicate()
    if subproc.returncode != 0:
        return None
    return stdout


def extract_links(text: str):
    return re.findall(r"\bhttps?://\S+", text)


# -------------------------------------------------
# Host handlers
# -------------------------------------------------
def gdrive(url: str) -> str:
    drive = "https://drive.google.com"
    reply = ""

    try:
        link = re.findall(r"\bhttps?://drive\.google\.com\S+", url)[0]
    except IndexError:
        return "`No Google Drive links found`\n"

    if "view" in link:
        file_id = link.split("/")[-2]
    elif "open?id=" in link:
        file_id = link.split("open?id=")[1]
    elif "uc?id=" in link:
        file_id = link.split("uc?id=")[1]
    else:
        return "`Invalid Google Drive link`\n"

    url = f"{drive}/uc?export=download&id={file_id}"
    download = requests.get(url, stream=True, allow_redirects=False)
    cookies = download.cookies

    if "location" in download.headers:
        dl_url = download.headers["location"]
        if "accounts.google.com" in dl_url:
            return "`Link is not public`\n"
        return f"[Direct Download]({dl_url})\n"

    page = BeautifulSoup(download.content, "html.parser")
    link_tag = page.find("a", {"id": "uc-download-link"})
    if not link_tag:
        return "`Failed to generate Drive link`\n"

    export = drive + link_tag.get("href")
    name = page.find("span", {"class": "uc-name-size"}).text
    response = requests.get(export, allow_redirects=False, cookies=cookies)

    dl_url = response.headers.get("location")
    if not dl_url:
        return "`Failed to generate Drive link`\n"

    return f"[{name}]({dl_url})\n"


def yandex_disk(url: str) -> str:
    api = "https://cloud-api.yandex.net/v1/disk/public/resources/download?public_key={}"
    try:
        link = re.findall(r"\bhttps?://.*yadi\.sk\S+", url)[0]
        data = requests.get(api.format(link)).json()
        name = data["href"].split("filename=")[1].split("&")[0]
        return f"[{name}]({data['href']})\n"
    except Exception:
        return "`Invalid Yandex Disk link`\n"


def mediafire(url: str) -> str:
    try:
        page = BeautifulSoup(requests.get(url).content, "lxml")
        info = page.find("a", {"aria-label": "Download file"})
        dl_url = info.get("href")
        size = re.findall(r"\(.*\)", info.text)[0]
        name = page.find("div", {"class": "filename"}).text
        return f"[{name} {size}]({dl_url})\n"
    except Exception:
        return "`Invalid MediaFire link`\n"


def sourceforge(url: str) -> str:
    try:
        file_path = re.findall(r"files(.*)/download", url)[0]
        project = re.findall(r"projects?/(.*?)/files", url)[0]
        mirrors = (
            f"https://sourceforge.net/settings/mirror_choices?"
            f"projectname={project}&filename={file_path}"
        )
        page = BeautifulSoup(requests.get(mirrors).content, "html.parser")
        items = page.find("ul", {"id": "mirrorList"}).findAll("li")[1:]

        reply = f"Mirrors for `{file_path.split('/')[-1]}`\n"
        for m in items:
            name = re.findall(r"\((.*)\)", m.text.strip())[0]
            dl_url = (
                f"https://{m['id']}.dl.sourceforge.net/project/"
                f"{project}/{file_path}"
            )
            reply += f"[{name}]({dl_url}) "
        return reply + "\n"
    except Exception:
        return "`Invalid SourceForge link`\n"


# -------------------------------------------------
# Handler
# -------------------------------------------------
async def handler(event, args):
    if args:
        message = " ".join(args)
    else:
        reply = await event.get_reply_message()
        if not reply or not reply.text:
            return await respond(
                event,
                "❌ **Usage:**\n"
                "`.direct <url>` or reply to a message containing links",
            )
        message = reply.text

    links = extract_links(message)
    if not links:
        return await respond(event, "`No links found.`")

    result = ""
    for link in links:
        if "drive.google.com" in link:
            result += gdrive(link)
        elif "yadi.sk" in link:
            result += yandex_disk(link)
        elif "mediafire.com" in link:
            result += mediafire(link)
        elif "sourceforge.net" in link:
            result += sourceforge(link)
        else:
            host = urllib.parse.urlparse(link).netloc
            result += f"`{host}` is not supported\n"

    await respond(event, result.strip())

import aiohttp
from bs4 import BeautifulSoup

from utils.respond import respond


__plugin__ = {
    "name": "XiaomiFirmware",
    "category": "utils",
    "description": (
        "Fetch latest MIUI / HyperOS firmware from Xiaomi Firmware Updater\n\n"
        "Usage:\n"
        ".hyper <device_codename>\n\n"
        "Example:\n"
        ".hyper sweet"
    ),
    "commands": {
        "hyper": "Get Xiaomi firmware (Recovery + Fastboot)",
    },
}


BASE_URL = "https://xmfirmwareupdater.com/firmware/{codename}/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Linux; Android 13; Pixel 7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Mobile Safari/537.36"
    )
}


async def fetch_firmware_page(codename):
    url = BASE_URL.format(codename=codename.lower())

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                return None
            return await resp.text()


def parse_firmware(html):
    soup = BeautifulSoup(html, "html.parser")

    results = {}

    # Each firmware entry is inside article.card (current structure)
    cards = soup.find_all("article")

    for card in cards:
        title_tag = card.find("h2")
        if not title_tag:
            continue

        title = title_tag.get_text(strip=True)

        # Extract region from title
        # Example title:
        # "Xiaomi Redmi Note 10 Pro (sweet) Global Recovery"
        region = None

        if "Global" in title:
            region = "Global"
        elif "India" in title:
            region = "India"
        elif "EEA" in title:
            region = "EEA"
        elif "China" in title:
            region = "China"
        elif "Russia" in title:
            region = "Russia"
        elif "Turkey" in title:
            region = "Turkey"
        elif "Indonesia" in title:
            region = "Indonesia"
        elif "Taiwan" in title:
            region = "Taiwan"

        if not region:
            continue

        if region not in results:
            results[region] = {
                "Recovery": None,
                "Fastboot": None,
            }

        # Find download links
        links = card.find_all("a")

        for link in links:
            href = link.get("href")
            text = link.get_text(strip=True)

            if not href:
                continue

            if "Recovery" in text:
                results[region]["Recovery"] = href
            elif "Fastboot" in text:
                results[region]["Fastboot"] = href

    return results


async def handler(event, args):
    if not args:
        return await respond(event, "Usage:\n.hyper <device_codename>")

    codename = args[0].lower()

    html = await fetch_firmware_page(codename)

    if not html:
        return await respond(event, "Device not found or site unreachable.")

    firmware_data = parse_firmware(html)

    if not firmware_data:
        return await respond(event, "No firmware data found.")

    text = f"**Xiaomi Firmware – {codename}**\n\n"

    for region, types in firmware_data.items():
        text += f"**{region}**\n"

        if types["Recovery"]:
            text += f"Recovery:\n{types['Recovery']}\n"

        if types["Fastboot"]:
            text += f"Fastboot:\n{types['Fastboot']}\n"

        text += "\n"

    await respond(event, text)
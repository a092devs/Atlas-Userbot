import aiohttp
from bs4 import BeautifulSoup

from utils.respond import respond


__plugin__ = {
    "name": "XiaomiFirmware",
    "category": "utils",
    "description": "Fetch latest MIUI/HyperOS firmware (Recovery + Fastboot) from Xiaomi Firmware Updater",
    "commands": {
        "hyper": "Get Xiaomi firmware info",
    },
}


BASE_URL = "https://xmfirmwareupdater.com/firmware/{codename}/"


REGION_MAP = {
    "MI": "Global",
    "EU": "EEA",
    "IN": "India",
    "CN": "China",
    "RU": "Russia",
    "TR": "Turkey",
    "ID": "Indonesia",
    "TW": "Taiwan",
}


async def fetch_firmware_page(codename):
    url = BASE_URL.format(codename=codename.lower())

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                return None
            return await resp.text()


def parse_firmware(html):
    soup = BeautifulSoup(html, "html.parser")

    results = {}

    cards = soup.find_all("div", class_="firmware")

    for card in cards:
        title = card.find("h5")
        if not title:
            continue

        title_text = title.get_text(strip=True)

        # Detect region from title
        region_code = None
        for code in REGION_MAP:
            if code in title_text:
                region_code = code
                break

        if not region_code:
            continue

        region_name = REGION_MAP.get(region_code, region_code)

        links = card.find_all("a")

        for link in links:
            href = link.get("href")
            text = link.get_text(strip=True)

            if not href:
                continue

            if region_name not in results:
                results[region_name] = {
                    "Recovery": None,
                    "Fastboot": None,
                }

            if "Recovery" in text:
                results[region_name]["Recovery"] = href
            elif "Fastboot" in text:
                results[region_name]["Fastboot"] = href

    return results


async def handler(event, args):
    if not args:
        return await respond(event, "Usage:\n.hyper <device_codename>")

    codename = args[0]

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
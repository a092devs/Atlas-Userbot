import aiohttp
import html

from utils.respond import respond


__plugin__ = {
    "name": "MedicineInfo",
    "category": "utils",
    "description": "Fetch information about medicines",
    "commands": {
        "med": "Get medicine information",
        "medicine": "Get medicine information",
    },
}


API_URL = "https://api.fda.gov/drug/label.json"


USAGE_TEXT = (
    "**Medicine Info**\n\n"
    "Usage:\n"
    "```\n"
    ".med <medicine name>\n"
    "```\n"
    "Example:\n"
    "```\n"
    ".med paracetamol\n"
    "```"
)


async def handler(event, args):
    if not args:
        return await respond(event, USAGE_TEXT)

    medicine = " ".join(args)

    await respond(event, "`Fetching medicine information...`")

    params = {
        "search": f"openfda.brand_name:{medicine}",
        "limit": 1,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(API_URL, params=params) as resp:
                data = await resp.json()

    except Exception as e:
        return await respond(event, f"Error fetching data:\n{e}")

    if "results" not in data:
        return await respond(event, f"No information found for **{medicine}**.")

    result = data["results"][0]

    def safe_get(field):
        value = result.get(field)
        if value and isinstance(value, list):
            return html.unescape(value[0])[:800]
        return "Not available"

    purpose = safe_get("purpose")
    indications = safe_get("indications_and_usage")
    warnings = safe_get("warnings")

    text = (
        f"**Medicine Information**\n\n"
        f"**Name:** {medicine}\n\n"
        f"**Purpose:**\n{purpose}\n\n"
        f"**Usage:**\n{indications}\n\n"
        f"**Warnings:**\n{warnings}"
    )

    await respond(event, text)
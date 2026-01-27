import aiohttp

from utils.respond import respond
from db.apikeys import get_key


__plugin__ = {
    "name": "Currency",
    "category": "utils",
    "description": "Convert between currencies using live exchange rates",
    "commands": {
        "currency": "Convert one currency to another",
        "cr": "Shortcut for currency conversion",
    },
}


API_URL = "https://v6.exchangerate-api.com/v6/{key}/pair"
REQUIRED_KEY = "CURRENCY_API_KEY"


USAGE_TEXT = (
    "**Currency Conversion**\n\n"
    "Usage:\n"
    "```\n"
    ".currency <FROM> <TO> [amount]\n"
    ".cr <amount> <FROM> <TO>\n"
    "```\n"
    "Examples:\n"
    "```\n"
    ".currency USD INR\n"
    ".cr 2 usd inr\n"
    "```"
)


async def handler(event, args):
    if len(args) < 2:
        return await respond(event, USAGE_TEXT)

    api_key = get_key(REQUIRED_KEY)
    if not api_key:
        return await respond(
            event,
            "Currency API key not configured.\n\n"
            f"Set it using:\n.setapi {REQUIRED_KEY} <your_api_key>",
        )

    cmd = event.raw_text.split()[0].lstrip("./").lower()

    try:
        # .cr format
        if cmd == "cr":
            amount = float(args[0])
            from_cur = args[1].upper()
            to_cur = args[2].upper()

        # .currency format
        else:
            from_cur = args[0].upper()
            to_cur = args[1].upper()
            amount = float(args[2]) if len(args) > 2 else 1.0

    except (IndexError, ValueError):
        return await respond(event, USAGE_TEXT)

    url = API_URL.format(key=api_key) + f"/{from_cur}/{to_cur}/{amount}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()

                if data.get("result") != "success":
                    return await respond(event, USAGE_TEXT)

    except Exception as e:
        return await respond(
            event,
            "Error fetching exchange rate:\n"
            f"{e}",
        )

    rate = data["conversion_rate"]
    result = data["conversion_result"]

    text = (
        "**Currency Conversion**\n\n"
        f"{amount:g} {from_cur} → {result:.2f} {to_cur}\n"
        f"Rate: 1 {from_cur} = {rate} {to_cur}"
    )

    await respond(event, text)

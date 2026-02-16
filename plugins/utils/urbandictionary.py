import aiohttp
import html

from utils.respond import respond


__plugin__ = {
    "name": "UrbanDictionary",
    "category": "utils",
    "description": "Search word definitions from Urban Dictionary",
    "commands": {
        "ud": "Search a word on Urban Dictionary",
        "urbandictionary": "Search a word on Urban Dictionary",
    },
}


API_URL = "https://api.urbandictionary.com/v0/define"


USAGE_TEXT = (
    "**Urban Dictionary**\n\n"
    "Usage:\n"
    "```\n"
    ".ud <word>\n"
    ".urbandictionary <word>\n"
    "```\n"
    "Example:\n"
    "```\n"
    ".ud atlas\n"
    "```"
)


async def handler(event, args):
    if not args:
        return await respond(event, USAGE_TEXT)

    word = " ".join(args)

    await respond(event, "`Searching Urban Dictionary...`")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(API_URL, params={"term": word}) as resp:
                data = await resp.json()

    except Exception as e:
        return await respond(
            event,
            "Error contacting Urban Dictionary:\n"
            f"{e}",
        )

    results = data.get("list", [])

    if not results:
        return await respond(event, f"No results found for **{word}**.")

    result = results[0]

    definition = html.escape(result.get("definition", "N/A"))
    example = html.escape(result.get("example", "N/A"))

    # Urban Dictionary formatting cleanup
    definition = definition.replace("[", "").replace("]", "")
    example = example.replace("[", "").replace("]", "")

    # Prevent Telegram message length issues
    if len(definition) > 1500:
        definition = definition[:1500] + "..."
    if len(example) > 800:
        example = example[:800] + "..."

    text = (
        "**Urban Dictionary**\n\n"
        f"**Word:** {word}\n\n"
        f"**Definition:**\n{definition}\n\n"
        f"**Example:**\n{example}"
    )

    await respond(event, text)
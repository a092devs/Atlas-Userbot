import aiohttp

from utils.respond import respond


__plugin__ = {
    "name": "MagiskRepoSearcher",
    "category": "utils",
    "description": "Search Magisk modules and get latest release link",
    "commands": {
        "mrepo": "Search Magisk modules",
    },
}

SEARCH_API = "https://api.github.com/search/repositories"
RELEASE_API = "https://api.github.com/repos/{owner}/{repo}/releases/latest"

SEARCH_CACHE = {}
RESULTS_PER_PAGE = 8


async def search_modules(query):
    params = {
        "q": f"{query} topic:magisk-module",
        "sort": "stars",
        "order": "desc",
        "per_page": 30,
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(SEARCH_API, params=params) as resp:
            return await resp.json()


async def get_latest_release(owner, repo):
    url = RELEASE_API.format(owner=owner, repo=repo)

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.json()


async def handler(event, args):
    chat_id = event.chat_id
    reply = await event.get_reply_message()

    # Handle reply navigation (n / p / number)
    if reply and chat_id in SEARCH_CACHE:
        reply_text = event.raw_text.strip().lower()

        cache = SEARCH_CACHE[chat_id]

        # Next page
        if reply_text == "n":
            cache["page"] += 1
            await event.delete()
            return await show_page(event, cache)

        # Previous page
        if reply_text == "p":
            cache["page"] = max(0, cache["page"] - 1)
            await event.delete()
            return await show_page(event, cache)

        # Selection
        if reply_text.isdigit():
            index = int(reply_text) - 1
            results = cache["results"]

            if index < 0 or index >= len(results):
                await event.delete()
                return await respond(event, "Invalid selection.")

            repo = results[index]
            owner = repo["owner"]["login"]
            name = repo["name"]

            await event.delete()
            await respond(event, "`Fetching latest release...`")

            release = await get_latest_release(owner, name)
            assets = release.get("assets", [])

            if not assets:
                return await respond(event, "No release assets found.")

            text = f"**{name} - Latest Release**\n\n"

            for asset in assets:
                text += f"{asset['name']}\n{asset['browser_download_url']}\n\n"

            return await respond(event, text)

    # New search
    if not args:
        return await respond(event, "Usage:\n.mrepo <module name>")

    query = " ".join(args)

    await respond(event, "`Searching Magisk modules...`")

    data = await search_modules(query)

    if "items" not in data or not data["items"]:
        return await respond(event, "No modules found.")

    results = data["items"]

    SEARCH_CACHE[chat_id] = {
        "results": results,
        "page": 0,
    }

    return await show_page(event, SEARCH_CACHE[chat_id])


async def show_page(event, cache):
    page = cache["page"]
    results = cache["results"]

    start = page * RESULTS_PER_PAGE
    end = start + RESULTS_PER_PAGE

    sliced = results[start:end]

    if not sliced:
        cache["page"] = max(0, page - 1)
        return await respond(event, "No more results.")

    total_pages = (len(results) - 1) // RESULTS_PER_PAGE + 1

    text = f"**Magisk Module Search** (Page {page+1}/{total_pages})\n\n"

    for i, repo in enumerate(sliced, start=start + 1):
        text += (
            f"{i}. **{repo['name']}**\n"
            f"⭐ {repo['stargazers_count']}\n"
            f"{repo['html_url']}\n\n"
        )

    text += "Reply with:\n"
    text += "`n` → next page\n"
    text += "`p` → previous page\n"
    text += "`number` → get release link"

    await respond(event, text)
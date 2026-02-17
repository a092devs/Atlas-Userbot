import aiohttp
import os

from utils.respond import respond

__plugin__ = {
    "name": "MagiskModuleSearcher",
    "category": "utils",
    "description": "Search and download Magisk modules from GitHub",
    "commands": {
        "magisk": "Search Magisk modules or download by number",
    },
}

SEARCH_API = "https://api.github.com/search/repositories"
RELEASE_API = "https://api.github.com/repos/{owner}/{repo}/releases/latest"

# In-memory cache per chat
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

    if not args:
        return await respond(event, "Usage:\n.magisk <module name>")

    query = " ".join(args).strip().lower()

    # Navigation
    if query in ("next", "prev") and chat_id in SEARCH_CACHE:
        cache = SEARCH_CACHE[chat_id]
        if query == "next":
            cache["page"] += 1
        else:
            cache["page"] = max(0, cache["page"] - 1)

        return await show_page(event, cache)

    # Selection
    if query.isdigit() and chat_id in SEARCH_CACHE:
        index = int(query) - 1
        cache = SEARCH_CACHE[chat_id]
        results = cache["results"]

        if index < 0 or index >= len(results):
            return await respond(event, "Invalid selection.")

        repo = results[index]
        owner = repo["owner"]["login"]
        name = repo["name"]

        await respond(event, "`Fetching latest release...`")

        release = await get_latest_release(owner, name)

        assets = release.get("assets", [])
        if not assets:
            return await respond(event, "No downloadable release found.")

        asset = assets[0]
        download_url = asset["browser_download_url"]
        filename = asset["name"]

        await respond(event, "`Downloading module...`")

        async with aiohttp.ClientSession() as session:
            async with session.get(download_url) as resp:
                content = await resp.read()

        with open(filename, "wb") as f:
            f.write(content)

        await event.client.send_file(
            event.chat_id,
            filename,
            caption=f"{name} - Latest Release"
        )

        os.remove(filename)
        return

    # New Search
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
        return await respond(event, "No more results.")

    total_pages = (len(results) - 1) // RESULTS_PER_PAGE + 1

    text = f"**Magisk Module Search** (Page {page+1}/{total_pages})\n\n"

    for i, repo in enumerate(sliced, start=start + 1):
        text += (
            f"{i}. **{repo['name']}**\n"
            f"⭐ {repo['stargazers_count']} | "
            f"{repo['html_url']}\n\n"
        )

    text += "Use `.magisk <number>` to download.\n"
    text += "Use `.magisk next` or `.magisk prev` to navigate."

    await respond(event, text)
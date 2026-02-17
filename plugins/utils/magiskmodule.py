import aiohttp
from datetime import datetime, timezone

from utils.respond import respond


__plugin__ = {
    "name": "MagiskRepoSearcher",
    "category": "utils",
    "description": "Search top active root/Magisk/KernelSU repositories",
    "commands": {
        "mrepo": "Search repositories",
    },
}

SEARCH_API = "https://api.github.com/search/repositories"
RELEASE_API = "https://api.github.com/repos/{owner}/{repo}/releases/latest"

SEARCH_CACHE = {}

MAX_RESULTS = 5
ACTIVE_MONTHS = 18


async def search_modules(query):
    params = {
        "q": f"{query} in:name,description",
        "sort": "stars",
        "order": "desc",
        "per_page": 20,
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(SEARCH_API, params=params) as resp:
            data = await resp.json()

    items = data.get("items", [])
    filtered = []

    now = datetime.now(timezone.utc)

    for repo in items:
        if repo.get("fork"):
            continue
        if repo.get("archived"):
            continue
        if repo.get("stargazers_count", 0) < 5:
            continue

        pushed_at = repo.get("pushed_at")
        if pushed_at:
            pushed_time = datetime.fromisoformat(
                pushed_at.replace("Z", "+00:00")
            )
            months_diff = (now - pushed_time).days / 30
            if months_diff > ACTIVE_MONTHS:
                continue

        filtered.append(repo)

        if len(filtered) >= MAX_RESULTS:
            break

    return filtered


async def get_latest_release(owner, repo):
    url = RELEASE_API.format(owner=owner, repo=repo)

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.json()


async def handler(event, args):
    chat_id = event.chat_id
    reply = await event.get_reply_message()

    # 🔥 Handle selection (must reply to bot message)
    if args and chat_id in SEARCH_CACHE and reply:
        me = await event.client.get_me()
        if reply.sender_id == me.id:

            cmd = args[0]
            if cmd.isdigit():
                results = SEARCH_CACHE[chat_id]
                index = int(cmd) - 1

                if 0 <= index < len(results):
                    repo = results[index]
                    owner = repo["owner"]["login"]
                    name = repo["name"]

                    await event.delete()

                    msg = await event.reply("Fetching latest release...")

                    release = await get_latest_release(owner, name)
                    assets = release.get("assets", [])

                    await msg.delete()

                    if not assets:
                        return await respond(event, "No release assets found.")

                    text = f"**{name} - Latest Release**\n\n"
                    for asset in assets:
                        text += f"{asset['name']}\n{asset['browser_download_url']}\n\n"

                    return await respond(event, text)

                await event.delete()
                return await respond(event, "Invalid selection.")

    # 🔍 New search
    if not args:
        return await respond(event, "Usage:\n.mrepo <repository name>")

    query = " ".join(args)

    search_msg = await event.reply("Searching repositories...")

    results = await search_modules(query)

    await search_msg.delete()

    if not results:
        return await respond(event, "No active repositories found.")

    SEARCH_CACHE[chat_id] = results

    text = "**Top Active Repositories**\n\n"

    for i, repo in enumerate(results, start=1):
        text += (
            f"{i}. **{repo['name']}**\n"
            f"⭐ {repo['stargazers_count']}\n"
            f"{repo['html_url']}\n\n"
        )

    text += "Reply with `.mrepo <number>` to get latest release."

    await respond(event, text)
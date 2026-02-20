from utils.respond import respond


__plugin__ = {
    "name": "Repository",
    "category": "system",
    "description": (
        "Show the official Atlas repository link.\n\n"
        "Usage:\n"
        "`.repo`"
    ),
    "commands": {
        "repo": "Show repository link",
    },
}


REPO_URL = "https://github.com/a092devs/Atlas-Userbot"


async def handler(event, args):
    text = (
        "<b>Atlas Userbot</b>\n\n"
        f"<a href='{REPO_URL}'>GitHub Repository</a>"
    )

    await respond(event, text)
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
        "**Atlas Userbot**\n\n"
        f"[GitHub Repository]({REPO_URL})"
    )

    await respond(event, text)
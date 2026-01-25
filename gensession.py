#!/usr/bin/env python3

import asyncio
import sys
from pathlib import Path

from telethon import TelegramClient
from telethon.sessions import StringSession

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def ask(msg):
    return input(msg).strip()


async def main():
    try:
        from config import config
        api_id = config.API_ID
        api_hash = config.API_HASH
    except Exception:
        api_id = int(ask("API_ID: "))
        api_hash = ask("API_HASH: ")

    async with TelegramClient(
        StringSession(),
        api_id,
        api_hash,
    ) as client:

        me = await client.get_me()
        session = client.session.save()

        await client.send_message(
            "me",
            "🔐 Atlas String Session\n\n"
            "DO NOT SHARE THIS\n\n"
            f"`{session}`"
        )

        print("Session sent to Saved Messages")

        if ask("Save session to .env? (y/N): ").lower() == "y":
            env = ROOT / ".env"
            content = env.read_text() if env.exists() else ""
            lines = [
                l for l in content.splitlines()
                if not l.startswith("STRING_SESSION=")
            ]
            lines.append(f"STRING_SESSION={session}")
            env.write_text("\n".join(lines) + "\n")
            print("Saved to .env")

        print(f"Logged in as {me.first_name}")


if __name__ == "__main__":
    asyncio.run(main())

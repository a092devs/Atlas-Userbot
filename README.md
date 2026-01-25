# Atlas Userbot

Atlas is a modular Telegram **userbot + assistant bot framework** built on **Telethon**.  
It focuses on clean architecture, extensibility, and safe GitHub-based updates.

---

## Features

- Modular plugin system
- Dual mode support (User / Bot)
- Unified command handler
- Advanced help system
- Safe restart and GitHub updates
- Owner-only control commands
- Admin and chat management tools
- Configurable log group

---

## Installation

### Clone the repository
```bash
git clone https://github.com/a092devs/Atlas-Userbot.git
cd Atlas-Userbot
```

### Create a virtual environment (recommended)
```bash
python3 -m venv venv
source venv/bin/activate
```

### Install dependencies
```bash
pip install -r requirements.txt
```

---

## Configuration

Create your environment file:
```bash
cp .env.example .env
```

Set the required values:
- API_ID
- API_HASH
- OWNER_ID
- BOT_TOKEN (optional)
- RUN_MODE=user or bot or dual

---

## Running Atlas

```bash
python run.py
```

If running for the first time:
```bash
python gensession.py
```

---

## Updating Atlas

Check for updates:
```
.update
```

Apply updates:
```
.update now
```

Atlas will pull the latest changes from GitHub and restart safely.

---

## Plugin Development

Each plugin must define metadata and a handler:

```python
__plugin__ = {
    "name": "Example",
    "category": "system",
    "description": "Example plugin",
    "commands": {
        "example": "Example command description",
    },
}

async def handler(event, args):
    ...
```

---

## Security

- Control commands are owner-only
- Updates are fast-forward only
- Runtime files, sessions, and databases are ignored by git

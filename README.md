# Atlas Userbot

Atlas is a modular Telegram **userbot + assistant bot framework** built on **Telethon**.  
It focuses on clean architecture, extensibility, and safe GitHub-based updates.

Atlas is designed to feel like a **framework**, not just another userbot.

---

## Features

- Modular plugin system
- Dual mode support (User / Bot / Dual)
- Unified command handler
- Advanced help system with grouped subcommands
- Safe restart and GitHub-based updates
- Owner-only control commands
- Admin and chat management tools
- Notes system
- Rule-based forwarder (PM, group, channel → anywhere)
- Media & album-safe forwarding
- YouTube / media downloader (yt-dlp)
- Server & runtime information
- Configurable log group
- Docker support

---

## Installation (Local)

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

- `API_ID`
- `API_HASH`
- `OWNER_ID`
- `STRING_SESSION` (for userbot)
- `BOT_TOKEN` (optional, for assistant bot)
- `RUN_MODE` (`user`, `bot`, or `dual`)

Generate a string session if needed:
```bash
python gensession.py
```

---

## Running Atlas (Local)

```bash
python run.py
```

---

## 🐳 Running Atlas with Docker (Recommended)

### Requirements
- Docker
- Docker Compose

---

### 1️⃣ Clone the repository
```bash
git clone https://github.com/a092devs/Atlas-Userbot.git
cd Atlas-Userbot
```

---

### 2️⃣ Create `.env`
```bash
cp .env.example .env
nano .env
```

Fill in:
- `API_ID`
- `API_HASH`
- `OWNER_ID`
- `STRING_SESSION`
- `BOT_TOKEN` (optional)
- `RUN_MODE`

---

### 3️⃣ Build & start Atlas
```bash
docker compose up -d --build
```

---

### 4️⃣ View logs
```bash
docker logs -f atlas-userbot
```

---

### 5️⃣ Stop Atlas
```bash
docker compose down
```

---

### 📦 Persistent data

All runtime data (database, logs, downloads) is stored in:
```
./data
```

Removing the container **will not delete your data**.

---

### 🎬 YTDL Note

Audio downloads require **ffmpeg**, which is already included in the Docker image.

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

Optional plugin lifecycle hooks:
```python
def init():
    ...
```

---

## Security

- Control commands are **owner-only**
- Updates are **fast-forward only**
- Runtime files, sessions, and databases are ignored by git

---

from pathlib import Path
from datetime import datetime

from utils.respond import respond
from config import config
from loader import loader
from log.logger import log_event


__plugin__ = {
    "name": "Modules",
    "category": "system",
    "description": "Manage Atlas modules (inspect, reload, export, install)",
    "commands": {
        "modules": "List installed modules",
        "modules info": "Show detailed module information",
        "modules check": "Validate a module for syntax errors",
        "modules reload": "Reload all modules",
        "modules upload": "Upload a module file",
        "modules uploadall": "Upload all installed modules",
        "modules install": "Install a module from replied .py file",
    },
}


PLUGIN_ROOT = Path(config.PLUGIN_PATH)


# -------------------------------------------------
# Helpers
# -------------------------------------------------
def scan_modules():
    found = {}
    for path in PLUGIN_ROOT.rglob("*.py"):
        if path.name.startswith("_"):
            continue
        found[path.stem.lower()] = path
    return found


def validate_source(source: str, name: str):
    try:
        compile(source, name, "exec")
        return True, None
    except Exception as e:
        return False, e


def extract_plugin_meta(source: str):
    scope = {}
    exec(source, scope)
    return scope.get("__plugin__")


# -------------------------------------------------
# Handler
# -------------------------------------------------
async def handler(event, args):
    module_map = scan_modules()

    # ---------------- .modules ----------------
    if not args:
        cats = {}
        for p in loader.plugins.values():
            cats.setdefault(p["category"], []).append(p["name"])

        text = "📦 **Installed Modules**\n\n"
        for cat in sorted(cats):
            text += f"**{cat.capitalize()}**\n"
            for name in sorted(cats[cat]):
                text += f"• `{name}`\n"
            text += "\n"

        text += (
            "Usage:\n"
            "`.modules info <module>`\n"
            "`.modules check <module>`\n"
            "`.modules reload`\n"
            "`.modules upload <module>`\n"
            "`.modules uploadall`\n"
            "`.modules install` (reply to .py)"
        )

        return await respond(event, text.strip())

    action = args[0].lower()

    # ---------------- install ----------------
    if action == "install":
        reply = await event.get_reply_message()
        if not reply or not reply.file or not reply.file.name.endswith(".py"):
            return await respond(
                event,
                "❌ Reply to a `.py` module file to install it.",
            )

        source = await reply.download_media(bytes)
        source = source.decode(errors="ignore")

        ok, error = validate_source(source, reply.file.name)
        if not ok:
            return await respond(
                event,
                f"❌ **Module validation failed**\n\n"
                f"`{type(error).__name__}: {error}`",
            )

        meta = extract_plugin_meta(source)
        if not meta:
            return await respond(event, "❌ `__plugin__` metadata not found.")

        name = meta.get("name")
        category = meta.get("category", "misc")

        if not name:
            return await respond(event, "❌ Module name missing in metadata.")

        filename = f"{name.lower()}.py"
        target_dir = PLUGIN_ROOT / category
        target_dir.mkdir(parents=True, exist_ok=True)
        target_file = target_dir / filename

        if target_file.exists():
            return await respond(
                event,
                f"❌ Module `{name}` already exists.\n"
                "Remove it first or rename the module.",
            )

        target_file.write_text(source, encoding="utf-8")

        loader.plugins.clear()
        loader.load()

        await log_event(
            event="Module Installed",
            details=f"{name} ({category})",
        )

        return await respond(
            event,
            f"✅ **Module installed successfully**\n\n"
            f"**Name:** `{name}`\n"
            f"**Category:** `{category}`",
        )

    # ---------------- reload ----------------
    if action == "reload":
        loader.plugins.clear()
        loader.load()
        return await respond(event, "🔄 **Modules reloaded successfully**")

    # ---------------- upload ----------------
    if action == "upload":
        if len(args) < 2:
            return await respond(event, "❌ Usage: `.modules upload <module>`")

        name = args[1].lower()
        path = module_map.get(name)
        if not path:
            return await respond(event, f"❌ Module `{name}` not found.")

        await event.client.send_file(
            event.chat_id,
            file=path,
            caption=f"📦 **Module:** `{path.name}`",
        )
        return

    # ---------------- uploadall ----------------
    if action == "uploadall":
        files = list(module_map.values())
        if not files:
            return await respond(event, "ℹ️ No modules found.")

        await event.client.send_file(
            event.chat_id,
            files,
            caption="📦 **All Installed Atlas Modules**",
        )
        return

    # ---------------- info ----------------
    if action == "info":
        if len(args) < 2:
            return await respond(event, "❌ Usage: `.modules info <module>`")

        name = args[1].lower()
        path = module_map.get(name)
        if not path:
            return await respond(event, f"❌ Module `{name}` not found.")

        size_kb = round(path.stat().st_size / 1024, 2)
        modified = datetime.fromtimestamp(path.stat().st_mtime)

        plugin = loader.plugins.get(name)

        text = (
            "📦 **Module Info**\n\n"
            f"**File:** `{path.name}`\n"
            f"**Category:** `{plugin['category'] if plugin else 'unknown'}`\n"
            f"**Path:** `{path}`\n"
            f"**Size:** `{size_kb} KB`\n"
            f"**Modified:** `{modified}`\n"
        )

        if plugin:
            text += "\n**Commands:**\n"
            for cmd, desc in plugin["commands"].items():
                text += f"• `.{cmd}` — {desc or 'No description'}\n"

        return await respond(event, text.strip())

    # ---------------- check ----------------
    if action == "check":
        if len(args) < 2:
            return await respond(event, "❌ Usage: `.modules check <module>`")

        name = args[1].lower()
        path = module_map.get(name)
        if not path:
            return await respond(event, f"❌ Module `{name}` not found.")

        ok, error = validate_source(path.read_text(), path.name)
        if ok:
            return await respond(event, f"✅ **Module `{name}` is valid**")

        return await respond(
            event,
            f"❌ **Validation failed**\n\n"
            f"`{type(error).__name__}: {error}`",
        )

    # ---------------- fallback ----------------
    await respond(event, "❌ Unknown subcommand. Use `.modules`.")	

from loader import loader
from utils.respond import respond


__plugin__ = {
    "name": "Help",
    "category": "system",
    "commands": ["help"],
    "description": "Show available modules and commands",
}


# -------------------------------------------------
# Category-wise help
# -------------------------------------------------
def build_category_help():
    categories = {}

    for plugin in loader.plugins.values():
        cat = plugin["category"]
        categories.setdefault(cat, []).append(plugin)

    text = "📘 **Atlas Help**\n"
    text += "Use `.help <module>` or `.help <command>` or `.help all`\n\n"

    for category in sorted(categories):
        items = sorted(categories[category], key=lambda x: x["name"])
        text += f"**{category.capitalize()}**\n"
        for p in items:
            text += f"  • **{p['name']}** — {p['description']}\n"
        text += "\n"

    return text.strip()


# -------------------------------------------------
# Module help
# -------------------------------------------------
def build_module_help(name: str):
    plugin = loader.plugins.get(name.lower())
    if not plugin:
        return None

    text = f"📦 **{plugin['name']}**\n\n"
    text += f"🗂 **Category:** `{plugin['category']}`\n"
    text += f"📝 **Description:** {plugin['description']}\n\n"

    text += "⚡ **Commands**\n"

    commands = plugin.get("commands", {})

    # -------------------------------------------------
    # Group commands by base command
    # -------------------------------------------------
    grouped = {}
    for cmd, desc in commands.items():
        parts = cmd.split()
        base = parts[0]
        sub = parts[1:] if len(parts) > 1 else []

        grouped.setdefault(base, []).append((sub, desc))

    # -------------------------------------------------
    # Render grouped commands
    # -------------------------------------------------
    for base in sorted(grouped):
        entries = grouped[base]

        # Base command description (if exists)
        base_desc = None
        for sub, desc in entries:
            if not sub:
                base_desc = desc
                break

        if base_desc:
            text += f"  • `.{base}` — {base_desc}\n"
        else:
            text += f"  • `.{base}`\n"

        # Subcommands
        for sub, desc in sorted(entries):
            if not sub:
                continue
            sub_name = " ".join(sub)
            if desc:
                text += f"      ◦ `{sub_name}` — {desc}\n"
            else:
                text += f"      ◦ `{sub_name}`\n"

    text += "\nℹ️ Use `.help <command>` to see command-specific help"

    return text.strip()



# -------------------------------------------------
# Command-level help
# -------------------------------------------------
def build_command_help(command: str):
    for plugin in loader.plugins.values():
        commands = plugin.get("commands", {})

        if command in commands:
            desc = commands.get(command) or plugin.get(
                "description", "No description available."
            )

            text = f"⌨️ **Command:** `.{command}`\n\n"
            text += f"📦 **Module:** `{plugin['name']}`\n"
            text += f"🗂 **Category:** `{plugin['category']}`\n\n"
            text += desc

            return text.strip()

    return None


# -------------------------------------------------
# All commands
# -------------------------------------------------
def build_all_commands():
    commands = sorted(
        f"`.{cmd}`"
        for plugin in loader.plugins.values()
        for cmd in plugin["commands"].keys()
    )

    if not commands:
        return "No commands available."

    text = "📜 **All Commands**\n\n"
    text += ", ".join(commands)
    text += "\n\nℹ️ Use `.help <module>` or `.help <command>`"

    return text


# -------------------------------------------------
# Handler
# -------------------------------------------------
async def handler(event, args):
    if args:
        arg = args[0].lower()

        if arg == "all":
            await respond(event, build_all_commands())
            return

        # 1️⃣ Try module help
        text = build_module_help(arg)
        if text:
            await respond(event, text)
            return

        # 2️⃣ Fallback to command help
        text = build_command_help(arg)
        if text:
            await respond(event, text)
            return

        # 3️⃣ Nothing found
        await respond(event, f"No module or command named `{arg}` found.")
        return

    await respond(event, build_category_help())

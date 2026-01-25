import importlib
import asyncio
from pathlib import Path

from dispatcher import dispatcher
from config import config
from utils.logger import log
from log.logger import log_event


class Loader:
    def __init__(self):
        self.path = Path(config.PLUGIN_PATH)
        self.plugins = {}  # plugin_name -> metadata

    def load(self):
        if not self.path.exists():
            log.warning("Plugins folder not found")
            return

        log.info("Loading plugins...")

        for file in self.path.rglob("*.py"):
            if file.name.startswith("_"):
                continue

            module_name = ".".join(file.with_suffix("").parts)

            try:
                module = importlib.import_module(module_name)

                meta = getattr(module, "__plugin__", None)
                handler = getattr(module, "handler", None)

                if not meta or not handler:
                    continue

                name = meta.get("name")
                category = meta.get("category", "misc")
                description = meta.get("description", "").strip()
                commands_meta = meta.get("commands", {})

                if not name or not commands_meta:
                    continue

                # Normalize commands:
                # list[str] -> {cmd: ""}
                # dict[str, str] -> unchanged
                if isinstance(commands_meta, list):
                    commands = {cmd: "" for cmd in commands_meta}
                elif isinstance(commands_meta, dict):
                    commands = commands_meta
                else:
                    continue

                # Store plugin metadata
                self.plugins[name.lower()] = {
                    "name": name,
                    "category": category,
                    "description": description,
                    "commands": commands,
                }

                # Register commands
                for cmd in commands.keys():
                    dispatcher.register(cmd, handler)

                # Console log ONLY (no Telegram spam)
                log.info(f"Loaded plugin: {name}")

            except Exception as e:
                # Console error (developer-facing)
                log.error(f"Failed to load plugin: {module_name}")
                log.error(str(e))

                # Telegram log (human-facing, best effort)
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(
                        log_event(
                            event="Plugin failed to load",
                            details=(
                                f"Plugin: {module_name}\n"
                                f"Reason: {e}"
                            ),
                        )
                    )
                except RuntimeError:
                    # Event loop not ready; ignore safely
                    pass


loader = Loader()

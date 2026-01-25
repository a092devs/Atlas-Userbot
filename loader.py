import importlib
import importlib.util
import asyncio
import subprocess
import sys
from pathlib import Path

from dispatcher import dispatcher
from config import config
from utils.logger import log
from log.logger import log_event


class Loader:
    def __init__(self):
        self.path = Path(config.PLUGIN_PATH)
        self.plugins = {}  # plugin_name -> metadata

    # -------------------------------------------------
    # Check if python module is already installed
    # -------------------------------------------------
    def _is_installed(self, module: str) -> bool:
        try:
            return importlib.util.find_spec(module) is not None
        except Exception:
            return False

    # -------------------------------------------------
    # Install python dependency
    # -------------------------------------------------
    def _install_package(self, package: str) -> bool:
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", package],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except Exception as e:
            log.error(f"Failed to install dependency '{package}': {e}")
            return False

    # -------------------------------------------------
    # Plugin loader
    # -------------------------------------------------
    def load(self):
        if not self.path.exists():
            log.warning("Plugins folder not found")
            return

        log.info("Loading plugins...")

        for file in self.path.rglob("*.py"):
            if file.name.startswith("_"):
                continue

            module_name = ".".join(file.with_suffix("").parts)
            module = None

            # ---------------------------------------------
            # Import with auto dependency resolution
            # ---------------------------------------------
            while True:
                try:
                    module = importlib.import_module(module_name)
                    break  # ✅ Import successful

                except ModuleNotFoundError as e:
                    missing = e.name

                    # If dependency is already installed, this is a real error
                    if self._is_installed(missing):
                        log.error(
                            f"Dependency '{missing}' already installed but import failed "
                            f"for {module_name}"
                        )
                        self._log_plugin_failure(module_name, e)
                        module = None
                        break

                    log.warning(
                        f"Missing dependency '{missing}' for {module_name}, installing..."
                    )

                    installed = self._install_package(missing)
                    if not installed:
                        self._log_plugin_failure(module_name, e)
                        module = None
                        break

                    # Log successful install
                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(
                            log_event(
                                event="Dependency Installed",
                                details=f"{missing} installed for {module_name}",
                            )
                        )
                    except RuntimeError:
                        pass

                    # Continue loop and retry import

                except Exception as e:
                    log.error(f"Failed to load plugin: {module_name}")
                    log.error(str(e))
                    self._log_plugin_failure(module_name, e)
                    module = None
                    break

            if not module:
                continue

            # ---------------------------------------------
            # Register plugin
            # ---------------------------------------------
            try:
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

                # Normalize commands
                if isinstance(commands_meta, list):
                    commands = {cmd: "" for cmd in commands_meta}
                elif isinstance(commands_meta, dict):
                    commands = commands_meta
                else:
                    continue

                self.plugins[name.lower()] = {
                    "name": name,
                    "category": category,
                    "description": description,
                    "commands": commands,
                }

                for cmd in commands.keys():
                    dispatcher.register(cmd, handler)

                log.info(f"Loaded plugin: {name}")

            except Exception as e:
                log.error(f"Failed to register plugin: {module_name}")
                log.error(str(e))
                self._log_plugin_failure(module_name, e)

    # -------------------------------------------------
    # Telegram error logger (safe)
    # -------------------------------------------------
    def _log_plugin_failure(self, module_name: str, error: Exception):
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(
                log_event(
                    event="Plugin failed to load",
                    details=f"Plugin: {module_name}\nReason: {error}",
                )
            )
        except RuntimeError:
            pass


loader = Loader()

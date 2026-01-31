import importlib
import importlib.util
import subprocess
import sys
from pathlib import Path

from dispatcher import dispatcher
from config import config
from utils.logger import log, log_event


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
                    break

                except ModuleNotFoundError as e:
                    missing = e.name

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

                    if not self._install_package(missing):
                        self._log_plugin_failure(module_name, e)
                        module = None
                        break

                    log_event(
                        event="Dependency Installed",
                        details=f"{missing} installed for {module_name}",
                    )

                except Exception as e:
                    log.error(f"Failed to load plugin: {module_name}")
                    log.error(str(e))
                    self._log_plugin_failure(module_name, e)
                    module = None
                    break

            if not module:
                continue

            # ---------------------------------------------
            # Auto-init plugin (DB / setup hook)
            # ---------------------------------------------
            init_fn = getattr(module, "init", None)
            if callable(init_fn):
                try:
                    init_fn()
                    log.info(f"Initialized plugin: {module_name}")
                except Exception as e:
                    log.error(f"Init failed for plugin: {module_name}")
                    log.error(str(e))
                    self._log_plugin_failure(module_name, e)
                    continue

            # ---------------------------------------------
            # Register NORMAL command plugins (unchanged)
            # ---------------------------------------------
            try:
                meta = getattr(module, "__plugin__", None)
                handler = getattr(module, "handler", None)

                if meta and handler:
                    name = meta.get("name")
                    category = meta.get("category", "misc")
                    description = meta.get("description", "").strip()
                    commands_meta = meta.get("commands", {})

                    if name and commands_meta:
                        if isinstance(commands_meta, list):
                            commands = {cmd: "" for cmd in commands_meta}
                        elif isinstance(commands_meta, dict):
                            commands = commands_meta
                        else:
                            commands = {}

                        if commands:
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

            # ---------------------------------------------
            # 🔥 REGISTER ASSISTANT PM HANDLERS (NEW)
            # ---------------------------------------------
            for attr in dir(module):
                fn = getattr(module, attr)
                if callable(fn) and getattr(fn, "_assistant_pm", False):
                    dispatcher.register(
                        f"__assistant_pm__{module_name}.{attr}",
                        fn,
                    )
                    log.info(
                        f"Registered assistant PM handler: {module_name}.{attr}"
                    )

        # -------------------------------------------------
        # Startup summary (SYNC)
        # -------------------------------------------------
        log_event(
            event="Plugins Loaded",
            details=f"{len(self.plugins)} plugins loaded successfully",
        )

    # -------------------------------------------------
    # Plugin failure logger (SYNC)
    # -------------------------------------------------
    def _log_plugin_failure(self, module_name: str, error: Exception):
        log_event(
            event="Plugin failed to load",
            details=f"Plugin: {module_name}\nReason: {error}",
        )


loader = Loader()

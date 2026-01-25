import os
import platform
import shutil
import time

from utils.respond import respond
from core.version import get_version


__plugin__ = {
    "name": "ServerInfo",
    "category": "system",
    "description": "Show server and runtime information",
    "commands": {
        "server": "Show server and runtime information",
    },
}


def _bytes_to_human(n):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.2f}{unit}"
        n /= 1024
    return f"{n:.2f}PB"


def _is_docker():
    if os.path.exists("/.dockerenv"):
        return True
    try:
        with open("/proc/1/cgroup") as f:
            data = f.read()
            return "docker" in data or "containerd" in data
    except Exception:
        return False


async def handler(event, args):
    version, codename = get_version()

    uname = platform.uname()
    cpu = platform.processor() or "Unknown"
    cores = os.cpu_count() or "?"

    total, used, free = shutil.disk_usage("/")

    mem_total = mem_used = "Unknown"
    try:
        with open("/proc/meminfo") as f:
            meminfo = f.read()

        total_kb = int(
            [l for l in meminfo.splitlines() if l.startswith("MemTotal")][0].split()[1]
        )
        avail_kb = int(
            [l for l in meminfo.splitlines() if l.startswith("MemAvailable")][0].split()[1]
        )

        mem_total = _bytes_to_human(total_kb * 1024)
        mem_used = _bytes_to_human((total_kb - avail_kb) * 1024)
    except Exception:
        pass

    uptime = "Unknown"
    try:
        with open("/proc/uptime") as f:
            seconds = float(f.read().split()[0])
            uptime = time.strftime("%Hh %Mm %Ss", time.gmtime(seconds))
    except Exception:
        pass

    text = (
        "Server Information\n\n"
        f"OS: `{uname.system} {uname.release}`\n"
        f"Kernel: `{uname.version.split()[0]}`\n"
        f"CPU: `{cpu}` ({cores} cores)\n"
        f"Memory: `{mem_used}` / `{mem_total}`\n"
        f"Disk: `{_bytes_to_human(used)}` / `{_bytes_to_human(total)}`\n"
        f"Uptime: `{uptime}`\n\n"
        f"Python: `{platform.python_version()}`\n"
        f"Docker: `{'Yes' if _is_docker() else 'No'}`\n"
        f"Atlas: `v{version} ({codename})`"
    )

    await respond(event, text)
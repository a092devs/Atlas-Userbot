import asyncio
import sys
import traceback
from io import StringIO

from utils.respond import respond
from config import config
from utils.logger import log_event


__plugin__ = {
    "name": "Eval",
    "category": "system",
    "description": "Evaluate Python, execute code, or run shell commands",
    "commands": {
        "eval": "Evaluate a Python expression",
        "exec": "Execute Python code",
        "sh": "Run a shell command",
    },
}


# -------------------------------------------------
# Helpers
# -------------------------------------------------
def is_owner(event):
    return event.sender_id == config.OWNER_ID


def get_code(event, args):
    if event.reply_to_msg_id:
        reply = event.reply_to_message
        if reply and reply.text:
            return reply.text.strip()

    if args:
        return " ".join(args).strip()

    return None


def stringify(obj):
    try:
        return str(obj)
    except Exception:
        return repr(obj)


def trim(text: str, limit: int = 4000) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "\n... (truncated)"


def format_response(title, code, output):
    return (
        f"**{title}**\n\n"
        f"Input:\n"
        f"```python\n{code}\n```\n"
        f"Output:\n"
        f"```python\n{trim(output)}\n```"
    )


# -------------------------------------------------
# Command handler
# -------------------------------------------------
async def handler(event, args):
    if not is_owner(event):
        return

    command = event.raw_text.split()[0].lstrip("./")
    code = get_code(event, args)

    if not code:
        return await respond(event, "No code provided.")

    # -------------------------------------------------
    # eval
    # -------------------------------------------------
    if command == "eval":
        try:
            result = eval(code, {"__builtins__": __builtins__}, {})
            output = stringify(result)

            await respond(
                event,
                format_response("Eval", code, output),
            )

        except Exception:
            error = traceback.format_exc()

            await respond(
                event,
                format_response("Eval Error", code, error),
            )

            log_event("Eval Error", error)

        return

    # -------------------------------------------------
    # exec
    # -------------------------------------------------
    if command == "exec":
        old_stdout = sys.stdout
        old_stderr = sys.stderr

        stdout = StringIO()
        stderr = StringIO()

        sys.stdout = stdout
        sys.stderr = stderr

        try:
            exec(code, {"__builtins__": __builtins__}, {})

            out = stdout.getvalue()
            err = stderr.getvalue()

            output = out or err or "Code executed successfully."

            await respond(
                event,
                format_response("Exec", code, output),
            )

        except Exception:
            error = traceback.format_exc()

            await respond(
                event,
                format_response("Exec Error", code, error),
            )

            log_event("Exec Error", error)

        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

        return

    # -------------------------------------------------
    # shell
    # -------------------------------------------------
    if command == "sh":
        try:
            process = await asyncio.create_subprocess_shell(
                code,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()
            output = (stdout or b"").decode() + (stderr or b"").decode()

            if not output.strip():
                output = "Command executed successfully."

            await respond(
                event,
                format_response("Shell", code, output),
            )

        except Exception:
            error = traceback.format_exc()

            await respond(
                event,
                format_response("Shell Error", code, error),
            )

            log_event("Shell Error", error)

        return
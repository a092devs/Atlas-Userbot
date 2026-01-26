import asyncio
import sys
import traceback
import subprocess
from io import StringIO

from utils.respond import respond
from config import config
from log.logger import log_event


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
    """
    Priority:
    1. Replied message text
    2. Inline arguments
    """
    if event.reply_to_msg_id:
        reply = event.reply_to_message
        if reply and reply.text:
            return reply.text.strip()

    if args:
        return " ".join(args).strip()

    return None


def trim_output(text: str, limit: int = 4000) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "\n… (truncated)"


# -------------------------------------------------
# Command handler
# -------------------------------------------------
async def handler(event, args):
    if not is_owner(event):
        return

    cmd = event.raw_text.split()[0].lstrip("./")
    code = get_code(event, args)

    if not code:
        return await respond(event, "❌ **No code provided.**")

    # -------------------------------------------------
    # .eval (expression)
    # -------------------------------------------------
    if cmd == "eval":
        try:
            result = eval(code, {"__builtins__": __builtins__}, {})
            output = repr(result)

            await respond(
                event,
                f"✅ **Eval Result:**\n```python\n{trim_output(output)}\n```",
            )

        except Exception:
            err = traceback.format_exc()
            await respond(
                event,
                f"❌ **Eval Error:**\n```python\n{trim_output(err)}\n```",
            )

            await log_event(
                event="Eval Error",
                details=err,
            )
        return

    # -------------------------------------------------
    # .exec (python block)
    # -------------------------------------------------
    if cmd == "exec":
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

            if not out and not err:
                out = "✓ Code executed successfully."

            text = out if out else err

            await respond(
                event,
                f"🧠 **Exec Output:**\n```python\n{trim_output(text)}\n```",
            )

        except Exception:
            err = traceback.format_exc()
            await respond(
                event,
                f"❌ **Exec Error:**\n```python\n{trim_output(err)}\n```",
            )

            await log_event(
                event="Exec Error",
                details=err,
            )

        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

        return

    # -------------------------------------------------
    # .sh (shell)
    # -------------------------------------------------
    if cmd == "sh":
        try:
            process = await asyncio.create_subprocess_shell(
                code,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            output = ""
            if stdout:
                output += stdout.decode()
            if stderr:
                output += stderr.decode()

            if not output.strip():
                output = "✓ Command executed successfully."

            await respond(
                event,
                f"🖥️ **Shell Output:**\n```bash\n{trim_output(output)}\n```",
            )

        except Exception:
            err = traceback.format_exc()
            await respond(
                event,
                f"❌ **Shell Error:**\n```python\n{trim_output(err)}\n```",
            )

            await log_event(
                event="Shell Error",
                details=err,
            )

        return
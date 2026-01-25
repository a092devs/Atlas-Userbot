import os
from db.core import db

LOG_KEY = "log_chat_id"
ENV_KEY = "LOG_CHANNEL_ID"


def init():
    # Loader lifecycle hook
    pass


def get_log_chat_id() -> int | None:
    # 1️⃣ Environment variable override (Docker-friendly)
    env_val = os.getenv(ENV_KEY)
    if env_val:
        try:
            return int(env_val)
        except Exception:
            pass

    # 2️⃣ Database-backed value
    row = db.execute(
        "SELECT value FROM kv_store WHERE key=?",
        (LOG_KEY,),
    ).fetchone()

    if not row:
        return None

    try:
        return int(row["value"])
    except Exception:
        return None


def set_log_chat_id(chat_id: int):
    db.execute(
        "INSERT OR REPLACE INTO kv_store (key, value) VALUES (?, ?)",
        (LOG_KEY, str(chat_id)),
    )


def remove_log_chat_id():
    db.execute(
        "DELETE FROM kv_store WHERE key=?",
        (LOG_KEY,),
    )


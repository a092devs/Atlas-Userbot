from db.core import db


LOG_KEY = "log_chat_id"


def get_log_chat_id() -> int | None:
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

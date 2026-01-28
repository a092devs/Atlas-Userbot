from db.core import db


def set_action(action, chat_id, message_id, git_head=None):
    db.execute(
        """
        INSERT INTO control_state (action, chat_id, message_id, status, git_head)
        VALUES (?, ?, ?, 'pending', ?)
        """,
        (action, chat_id, message_id, git_head),
    )


def get_pending():
    return db.execute(
        "SELECT * FROM control_state WHERE status='pending' ORDER BY id DESC LIMIT 1"
    ).fetchone()


def mark_done(action_id, status):
    db.execute(
        "UPDATE control_state SET status=? WHERE id=?",
        (status, action_id),
    )


def clear_all():
    db.execute("DELETE FROM control_state")


_LOG_CHAT_KEY = "log_chat_id"


def get_log_chat_id():
    row = db.execute(
        "SELECT value FROM kv_store WHERE key=?",
        (_LOG_CHAT_KEY,),
    ).fetchone()
    return int(row["value"]) if row else None


def set_log_chat_id(chat_id: int):
    db.execute(
        "INSERT OR REPLACE INTO kv_store (key, value) VALUES (?, ?)",
        (_LOG_CHAT_KEY, str(chat_id)),
    )


def clear_log_chat_id():
    db.execute(
        "DELETE FROM kv_store WHERE key=?",
        (_LOG_CHAT_KEY,),
    )


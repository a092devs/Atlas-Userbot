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

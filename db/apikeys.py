import sqlite3
from pathlib import Path

DB_PATH = Path("db/apikeys.db")


def _connect():
    DB_PATH.parent.mkdir(exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init():
    with _connect() as con:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS apikeys (
                name TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )


def set_key(name: str, value: str):
    with _connect() as con:
        con.execute(
            "REPLACE INTO apikeys (name, value) VALUES (?, ?)",
            (name.upper(), value),
        )


def get_key(name: str):
    with _connect() as con:
        cur = con.execute(
            "SELECT value FROM apikeys WHERE name = ?",
            (name.upper(),),
        )
        row = cur.fetchone()
        return row[0] if row else None


def delete_key(name: str):
    with _connect() as con:
        con.execute(
            "DELETE FROM apikeys WHERE name = ?",
            (name.upper(),),
        )


def list_keys():
    with _connect() as con:
        cur = con.execute("SELECT name FROM apikeys")
        return [row[0] for row in cur.fetchall()]

import sqlite3
import threading
from db.schema import SCHEMA
from utils.logger import log
from config import config


class Database:
    def __init__(self):
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(
            config.DB_FILE, check_same_thread=False
        )
        self._conn.row_factory = sqlite3.Row
        self._init()

    def _init(self):
        with self._lock:
            self._conn.executescript(SCHEMA)
            self._conn.commit()
        log.info("Database initialized")

    def execute(self, q, p=()):
        with self._lock:
            cur = self._conn.execute(q, p)
            self._conn.commit()
            return cur

    def get(self, key, default=None):
        row = self.execute(
            "SELECT value FROM kv_store WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else default

    def set(self, key, value):
        self.execute(
            "INSERT OR REPLACE INTO kv_store VALUES (?, ?)",
            (key, str(value)),
        )

    def delete(self, key):
        self.execute(
            "DELETE FROM kv_store WHERE key = ?",
            (key,),
        )

    def keys(self, prefix):
        rows = self.execute(
            "SELECT key FROM kv_store WHERE key LIKE ?",
            (f"{prefix}%",),
        ).fetchall()
        return [r["key"] for r in rows]


db = Database()

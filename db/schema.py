SCHEMA = """
-- =========================
-- Key-Value Store
-- =========================
CREATE TABLE IF NOT EXISTS kv_store (
    key TEXT PRIMARY KEY,
    value TEXT
);

-- =========================
-- Plugins State
-- =========================
CREATE TABLE IF NOT EXISTS plugins (
    name TEXT PRIMARY KEY,
    enabled INTEGER DEFAULT 1
);

-- =========================
-- Sudo / Admin Users
-- =========================
CREATE TABLE IF NOT EXISTS sudo_users (
    user_id INTEGER PRIMARY KEY
);

-- =========================
-- Control / Lifecycle State
-- =========================
-- Used to persist restart/update actions across restarts
-- Enables message edit after reboot & rollback on failure
CREATE TABLE IF NOT EXISTS control_state (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,              -- restart | update
    chat_id INTEGER NOT NULL,           -- chat where command was issued
    message_id INTEGER NOT NULL,        -- message to edit after restart
    status TEXT DEFAULT 'pending',      -- pending | success | failed
    git_head TEXT,                      -- previous git HEAD for rollback
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""

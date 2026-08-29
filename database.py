import sqlite3
from config import DB_PATH


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _connect()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            repo_url TEXT,
            runtime TEXT DEFAULT 'python',
            main_file TEXT DEFAULT 'main.py',
            status TEXT DEFAULT 'stopped',
            pid INTEGER DEFAULT 0,
            source_type TEXT DEFAULT '',
            error_message TEXT DEFAULT '',
            last_started TEXT DEFAULT '',
            last_stopped TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_projects_name ON projects(name)")
    conn.commit()
    conn.close()


def create_project(name, repo_url="", runtime="python", main_file="main.py", source_type=""):
    conn = _connect()
    try:
        conn.execute(
            "INSERT INTO projects (name, repo_url, runtime, main_file, source_type) VALUES (?, ?, ?, ?, ?)",
            (name, repo_url, runtime, main_file, source_type)
        )
        conn.commit()
        return conn.execute("SELECT id FROM projects WHERE name = ?", (name,)).fetchone()["id"]
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def get_all_projects():
    conn = _connect()
    rows = conn.execute("SELECT * FROM projects ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_project(project_id):
    conn = _connect()
    row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_project(project_id, **kwargs):
    allowed = {"name", "repo_url", "runtime", "main_file", "status", "pid", "source_type", "error_message", "last_started", "last_stopped"}
    fields = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return
    conn = _connect()
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    conn.execute(f"UPDATE projects SET {set_clause} WHERE id = ?", (*fields.values(), project_id))
    conn.commit()
    conn.close()


def update_project_status(project_id, status, pid=0):
    from datetime import datetime
    conn = _connect()
    if status == "running":
        conn.execute(
            "UPDATE projects SET status = ?, pid = ?, last_started = ?, error_message = '' WHERE id = ?",
            (status, pid, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), project_id)
        )
    elif status == "stopped":
        conn.execute(
            "UPDATE projects SET status = ?, pid = 0, last_stopped = ? WHERE id = ?",
            (status, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), project_id)
        )
    elif status == "error":
        conn.execute(
            "UPDATE projects SET status = ?, pid = 0 WHERE id = ?",
            (status, project_id)
        )
    else:
        conn.execute("UPDATE projects SET status = ? WHERE id = ?", (status, project_id))
    conn.commit()
    conn.close()


def delete_project(project_id):
    conn = _connect()
    conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    conn.commit()
    conn.close()


def get_setting(key, default=None):
    conn = _connect()
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key, value):
    conn = _connect()
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()


init_db()

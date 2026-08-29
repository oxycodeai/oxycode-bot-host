import sqlite3
import os
from datetime import datetime
from config import DB_PATH


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            repo_url TEXT DEFAULT '',
            runtime TEXT DEFAULT 'python',
            main_file TEXT DEFAULT 'main.py',
            status TEXT DEFAULT 'stopped',
            pid INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()


def create_project(name, repo_url="", runtime="python", main_file="main.py"):
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO projects (name, repo_url, runtime, main_file) VALUES (?, ?, ?, ?)",
        (name, repo_url, runtime, main_file)
    )
    project_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return project_id


def get_all_projects():
    conn = get_db()
    projects = conn.execute("SELECT * FROM projects ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(p) for p in projects]


def get_project(project_id):
    conn = get_db()
    project = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    conn.close()
    return dict(project) if project else None


def update_project_status(project_id, status, pid=0):
    conn = get_db()
    conn.execute(
        "UPDATE projects SET status = ?, pid = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (status, pid, project_id)
    )
    conn.commit()
    conn.close()


def update_project(project_id, **kwargs):
    conn = get_db()
    fields = []
    values = []
    for key, value in kwargs.items():
        if key in ("name", "repo_url", "runtime", "main_file"):
            fields.append(f"{key} = ?")
            values.append(value)
    if fields:
        fields.append("updated_at = CURRENT_TIMESTAMP")
        values.append(project_id)
        conn.execute(f"UPDATE projects SET {', '.join(fields)} WHERE id = ?", values)
        conn.commit()
    conn.close()


def delete_project(project_id):
    conn = get_db()
    conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    conn.commit()
    conn.close()


def get_setting(key, default=""):
    conn = get_db()
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key, value):
    conn = get_db()
    conn.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
        (key, value)
    )
    conn.commit()
    conn.close()


init_db()

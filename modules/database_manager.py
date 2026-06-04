from pathlib import Path
import sqlite3
from datetime import datetime


DB_PATH = Path("database") / "biomechanics.db"


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_database():
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sport TEXT NOT NULL,
                exercise TEXT NOT NULL,
                input_mode TEXT NOT NULL,
                source_file TEXT,
                results_folder TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        conn.commit()


def add_session(session_data):
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO analysis_sessions (
                sport,
                exercise,
                input_mode,
                source_file,
                results_folder,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            session_data.get("sport", ""),
            session_data.get("exercise", ""),
            session_data.get("input_mode", ""),
            session_data.get("source_file", ""),
            session_data.get("results_folder", ""),
            created_at
        ))

        conn.commit()


def get_recent_sessions(limit=5):
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM analysis_sessions
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()

    return [dict(row) for row in rows]


def get_session_count():
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) AS count
            FROM analysis_sessions
        """)

        row = cursor.fetchone()

    return row["count"] if row else 0
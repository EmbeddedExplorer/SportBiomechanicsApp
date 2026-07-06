from pathlib import Path
import sqlite3
from datetime import datetime


DB_PATH = Path("database") / "biomechanics.db"


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def column_exists(conn, table_name, column_name):
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()

    for col in columns:
        if col["name"] == column_name:
            return True

    return False


def session_folder_exists(results_folder):
    """
    Check whether a saved session folder still exists.

    This prevents Home page from showing old database records
    after the actual result folder was deleted from History.
    """

    if not results_folder:
        return False

    try:
        return Path(results_folder).exists()
    except Exception:
        return False


def cleanup_missing_sessions():
    """
    Remove database rows whose result folders no longer exist.

    This keeps:
        - Home page recent sessions
        - status bar session count
        - database records

    synchronized with the actual results/ folder.
    """

    removed_count = 0

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, results_folder
            FROM analysis_sessions
        """)

        rows = cursor.fetchall()

        missing_ids = []

        for row in rows:
            results_folder = row["results_folder"]

            if not session_folder_exists(results_folder):
                missing_ids.append(row["id"])

        for session_id in missing_ids:
            cursor.execute("""
                DELETE FROM analysis_sessions
                WHERE id = ?
            """, (session_id,))
            removed_count += 1

        conn.commit()

    return removed_count


def delete_session_by_results_folder(results_folder):
    """
    Delete a database record by its result folder path.

    This can be used later by HistoryPage after deleting a session folder.
    The cleanup_missing_sessions() function already handles this safely,
    but this helper is useful for direct synchronization.
    """

    if not results_folder:
        return

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM analysis_sessions
            WHERE results_folder = ?
        """, (str(results_folder),))

        conn.commit()


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

        # Safe migration for V8
        if not column_exists(conn, "analysis_sessions", "camera_view"):
            cursor.execute("""
                ALTER TABLE analysis_sessions
                ADD COLUMN camera_view TEXT DEFAULT 'N/A'
            """)

        conn.commit()

    cleanup_missing_sessions()


def add_session(session_data):
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO analysis_sessions (
                sport,
                exercise,
                camera_view,
                input_mode,
                source_file,
                results_folder,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            session_data.get("sport", ""),
            session_data.get("exercise", ""),
            session_data.get("camera_view", "N/A"),
            session_data.get("input_mode", ""),
            session_data.get("source_file", ""),
            session_data.get("results_folder", ""),
            created_at
        ))

        conn.commit()


def get_recent_sessions(limit=5):
    """
    Return only recent sessions whose result folders still exist.
    Old deleted sessions are automatically removed from the database.
    """

    cleanup_missing_sessions()

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
    """
    Return count of valid sessions only.
    Deleted/missing result folders are cleaned before counting.
    """

    cleanup_missing_sessions()

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) AS count
            FROM analysis_sessions
        """)

        row = cursor.fetchone()

    return row["count"] if row else 0
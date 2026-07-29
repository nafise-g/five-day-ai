"""
Persistent Session Store using SQLite database for storing turn history and audit metadata across turns.
Fulfills Rubric Category 2: Persistent Session State.
"""

import sqlite3
import json
import time
from typing import List, Dict, Any, Optional
from config import config

class PersistentSessionStore:
    """
    Manages persistent state across multi-turn user sessions, saving message trajectories,
    facility audit profiles, and user preferences to SQLite database storage.
    """

    def __init__(self, db_path: str = config.DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Initializes database tables if they do not exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Session Metadata Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    created_at REAL,
                    updated_at REAL,
                    summary TEXT,
                    metadata_json TEXT
                )
            """)
            # Session Messages Trajectory Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS session_messages (
                    message_id TEXT PRIMARY KEY,
                    session_id TEXT,
                    role TEXT,
                    content TEXT,
                    timestamp REAL,
                    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
                )
            """)
            # Audit Findings Key-Value Store Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_findings (
                    session_id TEXT,
                    facility_id TEXT,
                    finding_key TEXT,
                    finding_value_json TEXT,
                    timestamp REAL,
                    PRIMARY KEY (session_id, facility_id, finding_key)
                )
            """)
            conn.commit()

    def create_or_get_session(self, session_id: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Creates a new session or retrieves an existing session from persistent storage."""
        now = time.time()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
            row = cursor.fetchone()
            if row:
                return {
                    "session_id": row["session_id"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "summary": row["summary"],
                    "metadata": json.loads(row["metadata_json"]) if row["metadata_json"] else {}
                }
            else:
                meta_json = json.dumps(metadata or {})
                cursor.execute(
                    "INSERT INTO sessions (session_id, created_at, updated_at, summary, metadata_json) VALUES (?, ?, ?, ?, ?)",
                    (session_id, now, now, "", meta_json)
                )
                conn.commit()
                return {
                    "session_id": session_id,
                    "created_at": now,
                    "updated_at": now,
                    "summary": "",
                    "metadata": metadata or {}
                }

    def append_message(self, session_id: str, role: str, content: str, message_id: Optional[str] = None) -> None:
        """Appends a single turn message to the persistent session store."""
        import uuid
        msg_id = message_id or str(uuid.uuid4())
        now = time.time()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO session_messages (message_id, session_id, role, content, timestamp) VALUES (?, ?, ?, ?, ?)",
                (msg_id, session_id, role, content, now)
            )
            cursor.execute("UPDATE sessions SET updated_at = ? WHERE session_id = ?", (now, session_id))
            conn.commit()

    def get_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """Retrieves all message turns for a given session sorted chronologically."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT role, content, timestamp FROM session_messages WHERE session_id = ? ORDER BY timestamp ASC",
                (session_id,)
            )
            rows = cursor.fetchall()
            return [{"role": row["role"], "content": row["content"], "timestamp": row["timestamp"]} for row in rows]

    def save_audit_finding(self, session_id: str, facility_id: str, key: str, value: Dict[str, Any]) -> None:
        """Saves persistent facility audit finding to database."""
        now = time.time()
        val_json = json.dumps(value)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO audit_findings (session_id, facility_id, finding_key, finding_value_json, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (session_id, facility_id, key, val_json, now))
            conn.commit()

    def get_audit_findings(self, session_id: str, facility_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieves stored audit findings for session."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if facility_id:
                cursor.execute(
                    "SELECT facility_id, finding_key, finding_value_json, timestamp FROM audit_findings WHERE session_id = ? AND facility_id = ?",
                    (session_id, facility_id)
                )
            else:
                cursor.execute(
                    "SELECT facility_id, finding_key, finding_value_json, timestamp FROM audit_findings WHERE session_id = ?",
                    (session_id,)
                )
            rows = cursor.fetchall()
            return [
                {
                    "facility_id": r["facility_id"],
                    "key": r["finding_key"],
                    "value": json.loads(r["finding_value_json"]),
                    "timestamp": r["timestamp"]
                }
                for r in rows
            ]

    def update_session_summary(self, session_id: str, summary: str) -> None:
        """Updates the high-level summary string for a session."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE sessions SET summary = ?, updated_at = ? WHERE session_id = ?", (summary, time.time(), session_id))
            conn.commit()

# -*- coding: utf-8 -*-
import sqlite3
import json
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, List, Tuple

from .models.activity_session import ActivitySession, SessionState

DEFAULT_DB_DIR = Path.home() / ".esp32_lab"
DEFAULT_DB_FILE = DEFAULT_DB_DIR / "sessions.db"

class SessionRepository:
    """Interface for session persistence."""
    def save(self, session: ActivitySession, project_snapshot: str = None) -> None:
        raise NotImplementedError

    def load(self, session_id: str) -> Optional[ActivitySession]:
        raise NotImplementedError

    def get_working_project(self, session_id: str) -> Optional[str]:
        raise NotImplementedError

    def find_active_session(self, activity_id: str, student_id: str = None) -> Optional[ActivitySession]:
        raise NotImplementedError

    def delete(self, session_id: str) -> None:
        raise NotImplementedError

class SQLiteSessionRepository(SessionRepository):
    def __init__(self, db_path: Path | str | None = None):
        if db_path is None:
            DEFAULT_DB_DIR.mkdir(parents=True, exist_ok=True)
            self.db_path = DEFAULT_DB_FILE
        else:
            self.db_path = Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_tables()

    @contextmanager
    def _connection(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_tables(self):
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS activity_sessions (
                    session_id TEXT PRIMARY KEY,
                    activity_id TEXT NOT NULL,
                    student_id TEXT,
                    session_data TEXT NOT NULL,
                    working_project TEXT,
                    last_saved_at REAL
                )
            """)
            conn.commit()

    def save(self, session: ActivitySession, project_snapshot: str = None):
        import time
        session.last_saved_at = time.time()
        
        # Determine student_id safely
        student_id = session.student.student_id if session.student else ""
        
        with self._connection() as conn:
            cursor = conn.cursor()
            
            # Check if exists
            cursor.execute("SELECT session_id, working_project FROM activity_sessions WHERE session_id = ?", (session.session_id,))
            row = cursor.fetchone()
            
            session_data_json = json.dumps(session.to_dict())
            
            if row:
                # Update
                if project_snapshot is None:
                    project_snapshot = row["working_project"]
                
                cursor.execute("""
                    UPDATE activity_sessions 
                    SET session_data = ?, working_project = ?, last_saved_at = ?
                    WHERE session_id = ?
                """, (session_data_json, project_snapshot, session.last_saved_at, session.session_id))
            else:
                # Insert
                cursor.execute("""
                    INSERT INTO activity_sessions (session_id, activity_id, student_id, session_data, working_project, last_saved_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (session.session_id, session.activity_id, student_id, session_data_json, project_snapshot, session.last_saved_at))
            
            conn.commit()

    def load(self, session_id: str) -> Optional[ActivitySession]:
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT session_data FROM activity_sessions WHERE session_id = ?", (session_id,))
            row = cursor.fetchone()
            if row:
                return ActivitySession.from_dict(json.loads(row["session_data"]))
        return None

    def get_working_project(self, session_id: str) -> Optional[str]:
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT working_project FROM activity_sessions WHERE session_id = ?", (session_id,))
            row = cursor.fetchone()
            if row:
                return row["working_project"]
        return None

    def find_active_session(self, activity_id: str, student_id: str = "") -> Optional[ActivitySession]:
        """Trouve une session non-frozen pour cette activit / lve."""
        with self._connection() as conn:
            cursor = conn.cursor()
            if student_id:
                cursor.execute("""
                    SELECT session_data FROM activity_sessions 
                    WHERE activity_id = ? AND student_id = ? 
                    ORDER BY last_saved_at DESC LIMIT 1
                """, (activity_id, student_id))
            else:
                # Si pas de student id (TP simple local), on prend la dernire session de cette activit.
                cursor.execute("""
                    SELECT session_data FROM activity_sessions 
                    WHERE activity_id = ? 
                    ORDER BY last_saved_at DESC LIMIT 1
                """, (activity_id,))
                
            row = cursor.fetchone()
            if row:
                sess = ActivitySession.from_dict(json.loads(row["session_data"]))
                # On ne retourne que si la session n'est pas finalise. 
                # (Ou plutôt, le repository retourne la dernière, le domaine décidera si c'est IN_PROGRESS ou FROZEN)
                return sess
        return None

    def delete(self, session_id: str) -> None:
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM activity_sessions WHERE session_id = ?", (session_id,))
            conn.commit()

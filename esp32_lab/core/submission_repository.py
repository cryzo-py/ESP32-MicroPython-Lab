# -*- coding: utf-8 -*-
import sqlite3
import json
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, List

from .models.submission import Submission

DEFAULT_DB_DIR = Path.home() / ".esp32_lab"
DEFAULT_DB_FILE = DEFAULT_DB_DIR / "sessions.db"

class SubmissionRepository:
    def save(self, submission: Submission) -> None:
        raise NotImplementedError

    def load(self, submission_id: str) -> Optional[Submission]:
        raise NotImplementedError
        
    def find_by_session(self, session_id: str) -> Optional[Submission]:
        raise NotImplementedError

    def delete(self, submission_id: str) -> None:
        raise NotImplementedError
        
    def get_submissions_for_activity(self, activity_id: str) -> List[Submission]:
        raise NotImplementedError

class SQLiteSubmissionRepository(SubmissionRepository):
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
                CREATE TABLE IF NOT EXISTS activity_submissions (
                    submission_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL UNIQUE,
                    activity_id TEXT NOT NULL,
                    student_id TEXT,
                    submission_data TEXT NOT NULL,
                    submitted_at REAL
                )
            """)
            conn.commit()

    def save(self, submission: Submission):
        student_id = submission.student_identity.student_id if submission.student_identity else ""
        submission_json = json.dumps(submission.to_dict())
        
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT submission_id FROM activity_submissions WHERE submission_id = ?", (submission.submission_id,))
            row = cursor.fetchone()
            if row:
                cursor.execute("""
                    UPDATE activity_submissions 
                    SET submission_data = ?, submitted_at = ?
                    WHERE submission_id = ?
                """, (submission_json, submission.submitted_at, submission.submission_id))
            else:
                cursor.execute("""
                    INSERT INTO activity_submissions (submission_id, session_id, activity_id, student_id, submission_data, submitted_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (submission.submission_id, submission.session_id, submission.activity_id, student_id, submission_json, submission.submitted_at))
            conn.commit()

    def load(self, submission_id: str) -> Optional[Submission]:
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT submission_data FROM activity_submissions WHERE submission_id = ?", (submission_id,))
            row = cursor.fetchone()
            if row:
                return Submission.from_dict(json.loads(row["submission_data"]))
        return None

    def find_by_session(self, session_id: str) -> Optional[Submission]:
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT submission_data FROM activity_submissions WHERE session_id = ?", (session_id,))
            row = cursor.fetchone()
            if row:
                return Submission.from_dict(json.loads(row["submission_data"]))
        return None
        
    def get_submissions_for_activity(self, activity_id: str) -> List[Submission]:
        subs = []
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT submission_data FROM activity_submissions WHERE activity_id = ? ORDER BY submitted_at DESC", (activity_id,))
            rows = cursor.fetchall()
            for row in rows:
                subs.append(Submission.from_dict(json.loads(row["submission_data"])))
        return subs

    def delete(self, submission_id: str) -> None:
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM activity_submissions WHERE submission_id = ?", (submission_id,))
            conn.commit()

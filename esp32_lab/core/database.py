"""
Persistance locale SQLite pour le suivi pédagogique des apprenants
Enregistre l'historique des évaluations des TPs, les notes obtenues, et les compétences validées.
"""

import os
from contextlib import contextmanager
from pathlib import Path
import sqlite3
from typing import Any

from .evaluator import EvaluationResult

DEFAULT_DB_DIR = Path.home() / ".esp32_lab"
DEFAULT_DB_FILE = DEFAULT_DB_DIR / "progress.db"


class ProgressDatabase:
    """Gestionnaire de base de données SQLite locale pour la progression de l'apprenant."""

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
                CREATE TABLE IF NOT EXISTS tp_evaluations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lesson_id TEXT NOT NULL,
                    lesson_title TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    max_score INTEGER NOT NULL,
                    passed INTEGER NOT NULL,
                    evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    code_snippet TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS achievements (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def record_evaluation(self, result: EvaluationResult, code_snippet: str = "") -> int:
        """Enregistre le résultat d'une évaluation automatique."""
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tp_evaluations (lesson_id, lesson_title, score, max_score, passed, code_snippet)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                result.lesson_id,
                result.lesson_title,
                result.score,
                result.max_score,
                1 if result.passed else 0,
                code_snippet
            ))
            eval_id = cursor.lastrowid
            conn.commit()
            return eval_id

    def get_completed_lessons(self) -> set[str]:
        """Renvoie l'ensemble des identifiants de leçons validées (score >= 70)."""
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT lesson_id FROM tp_evaluations WHERE passed = 1")
            rows = cursor.fetchall()
            return {row["lesson_id"] for row in rows}

    def get_best_score(self, lesson_id: str) -> int | None:
        """Renvoie la meilleure note obtenue pour un TP donné."""
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(score) as best FROM tp_evaluations WHERE lesson_id = ?", (lesson_id,))
            row = cursor.fetchone()
            return row["best"] if row and row["best"] is not None else None

    def get_summary_stats(self) -> dict[str, Any]:
        """Renvoie un résumé statistique de l'apprentissage."""
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(DISTINCT lesson_id) as passed_count FROM tp_evaluations WHERE passed = 1")
            passed_count = cursor.fetchone()["passed_count"]

            cursor.execute("SELECT COUNT(*) as total_attempts, AVG(score) as avg_score FROM tp_evaluations")
            row = cursor.fetchone()
            total_attempts = row["total_attempts"]
            avg_score = round(row["avg_score"], 1) if row["avg_score"] is not None else 0.0

            return {
                "passed_lessons": passed_count,
                "total_attempts": total_attempts,
                "average_score": avg_score,
            }


_db_instance: ProgressDatabase | None = None


def get_progress_db() -> ProgressDatabase:
    global _db_instance
    if _db_instance is None:
        _db_instance = ProgressDatabase()
    return _db_instance

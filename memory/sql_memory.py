import os
from typing import Any, Dict, List
from sqlalchemy import create_engine, text


class SQLMemory:
    """Lightweight storage for logs/issues. Uses SQLite by default or Postgres
    when `DATABASE_URL` is set in environment.

    The class will create tables if they don't exist using a simple migration.
    """

    def __init__(self, path: str = ".memory.db"):
        # Allow DATABASE_URL override for Postgres or any SQLAlchemy URL
        db_url = os.environ.get("DATABASE_URL")
        if db_url:
            self.engine = create_engine(db_url, future=True)
            self._ensure_migrations(engine=self.engine, dialect='postgres')
        else:
            # sqlite file
            self.engine = create_engine(f"sqlite:///{path}", future=True)
            # For sqlite, create tables if needed
            self._ensure_migrations(engine=self.engine, dialect='sqlite')

    def _ensure_migrations(self, engine, dialect: str = 'sqlite'):
        # Apply a minimal migration: create logs and issues if not exists.
        if dialect == 'postgres':
            create_logs = """
            CREATE TABLE IF NOT EXISTS logs (
                id SERIAL PRIMARY KEY,
                agent TEXT,
                action TEXT,
                detail TEXT,
                ts TIMESTAMP WITH TIME ZONE DEFAULT now()
            );
            """
            create_issues = """
            CREATE TABLE IF NOT EXISTS issues (
                id SERIAL PRIMARY KEY,
                source TEXT,
                detail TEXT,
                severity TEXT,
                ts TIMESTAMP WITH TIME ZONE DEFAULT now()
            );
            """
        else:
            # sqlite dialect
            create_logs = """
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent TEXT,
                action TEXT,
                detail TEXT,
                ts DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """
            create_issues = """
            CREATE TABLE IF NOT EXISTS issues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT,
                detail TEXT,
                severity TEXT,
                ts DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """

        with engine.begin() as conn:
            conn.execute(text(create_logs))
            conn.execute(text(create_issues))

    def log(self, agent: str, action: str, detail: str):
        stmt = text("INSERT INTO logs(agent, action, detail) VALUES (:a, :ac, :d)")
        with self.engine.begin() as conn:
            conn.execute(stmt, {"a": agent, "ac": action, "d": detail})

    def add_issue(self, source: str, detail: str, severity: str = "medium"):
        stmt = text("INSERT INTO issues(source, detail, severity) VALUES (:s, :d, :sev)")
        with self.engine.begin() as conn:
            conn.execute(stmt, {"s": source, "d": detail, "sev": severity})

    def query_logs(self, limit: int = 100) -> List[tuple]:
        stmt = text("SELECT id, agent, action, detail, ts FROM logs ORDER BY id DESC LIMIT :limit")
        with self.engine.connect() as conn:
            res = conn.execute(stmt, {"limit": limit})
            return res.fetchall()

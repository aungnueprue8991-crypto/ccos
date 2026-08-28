"""AGS SQLite persistence — agent-local developmental state."""

from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

_DEFAULT_PATH: Optional[Path] = None
_LOCAL = threading.local()


def configure(db_path: str | Path) -> None:
    global _DEFAULT_PATH
    _DEFAULT_PATH = Path(db_path)
    _DEFAULT_PATH.parent.mkdir(parents=True, exist_ok=True)


def jdump(obj: Any) -> str:
    return json.dumps(obj, default=str, separators=(",", ":"))


def jload(raw: Any, default: Any = None) -> Any:
    if raw is None:
        return default if default is not None else {}
    if isinstance(raw, (dict, list)):
        return raw
    try:
        return json.loads(raw)
    except Exception:
        return default if default is not None else {}


class AGSDatabase:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.path), check_same_thread=False, timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    @contextmanager
    def tx(self):
        conn = self._connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def execute(self, sql: str, params: tuple = ()) -> None:
        with self.tx() as conn:
            conn.execute(sql, params)

    def fetchone(self, sql: str, params: tuple = ()) -> Optional[Dict]:
        conn = self._connect()
        try:
            row = conn.execute(sql, params).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def fetchall(self, sql: str, params: tuple = ()) -> List[Dict]:
        conn = self._connect()
        try:
            return [dict(r) for r in conn.execute(sql, params).fetchall()]
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self.tx() as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS genomes (
                genome_id TEXT PRIMARY KEY,
                agent_id TEXT,
                traits TEXT,
                parent_a TEXT,
                parent_b TEXT,
                generation INTEGER DEFAULT 0,
                mutations TEXT,
                created_at REAL
            );
            CREATE INDEX IF NOT EXISTS idx_genomes_agent ON genomes(agent_id);

            CREATE TABLE IF NOT EXISTS episodes (
                episode_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                description TEXT,
                context TEXT,
                outcome TEXT,
                valence REAL DEFAULT 0,
                importance REAL DEFAULT 0.5,
                tags TEXT,
                created_at REAL
            );
            CREATE INDEX IF NOT EXISTS idx_ep_agent ON episodes(agent_id);

            CREATE TABLE IF NOT EXISTS knowledge (
                item_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                content TEXT,
                domain TEXT,
                confidence REAL,
                evidence TEXT,
                source TEXT,
                source_type TEXT,
                verified INTEGER DEFAULT 0,
                tags TEXT,
                access_count INTEGER DEFAULT 0,
                created_at REAL,
                updated_at REAL
            );
            CREATE INDEX IF NOT EXISTS idx_know_agent ON knowledge(agent_id);

            CREATE TABLE IF NOT EXISTS self_model (
                entry_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                dimension TEXT,
                value REAL,
                description TEXT,
                evidence TEXT,
                updated_at REAL,
                UNIQUE(agent_id, dimension)
            );

            CREATE TABLE IF NOT EXISTS world_model (
                fact_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                entity TEXT,
                property TEXT,
                value TEXT,
                confidence REAL,
                evidence TEXT,
                created_at REAL,
                updated_at REAL,
                UNIQUE(agent_id, entity, property)
            );
            CREATE INDEX IF NOT EXISTS idx_wm_agent ON world_model(agent_id);

            CREATE TABLE IF NOT EXISTS agents_meta (
                agent_id TEXT PRIMARY KEY,
                identity TEXT,
                genome_id TEXT,
                status TEXT,
                state_json TEXT,
                created_at REAL,
                updated_at REAL
            );

            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                applied_at REAL,
                notes TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_ep_agent_time ON episodes(agent_id, created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_ep_agent_importance ON episodes(agent_id, importance DESC);
            CREATE INDEX IF NOT EXISTS idx_know_agent_domain ON knowledge(agent_id, domain);
            CREATE INDEX IF NOT EXISTS idx_know_agent_conf ON knowledge(agent_id, confidence DESC);
            CREATE INDEX IF NOT EXISTS idx_wm_entity ON world_model(agent_id, entity);
            CREATE INDEX IF NOT EXISTS idx_wm_prop ON world_model(agent_id, property);
            CREATE INDEX IF NOT EXISTS idx_self_agent ON self_model(agent_id);
            """)
            try:
                conn.executescript("""
                CREATE VIRTUAL TABLE IF NOT EXISTS episodes_fts USING fts5(
                    episode_id UNINDEXED,
                    agent_id UNINDEXED,
                    description,
                    outcome,
                    content='episodes',
                    content_rowid='rowid'
                );
                CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
                    item_id UNINDEXED,
                    agent_id UNINDEXED,
                    content,
                    domain,
                    content='knowledge',
                    content_rowid='rowid'
                );
                """)
            except Exception:
                pass
            row = conn.execute("SELECT COUNT(*) AS c FROM schema_version").fetchone()
            if row and int(row["c"] if hasattr(row, "keys") else row[0]) == 0:
                import time
                conn.execute(
                    "INSERT INTO schema_version(version, applied_at, notes) VALUES (2, ?, ?)",
                    (time.time(), "indexes+fts5+schema_version"),
                )

    def fts_available(self) -> bool:
        row = self.fetchone(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='episodes_fts'"
        )
        return row is not None

    def search_episodes_fts(self, agent_id: str, query: str, limit: int = 10) -> List[Dict]:
        if not self.fts_available() or not query.strip():
            return self.fetchall(
                "SELECT * FROM episodes WHERE agent_id=? AND (description LIKE ? OR outcome LIKE ?) "
                "ORDER BY importance DESC LIMIT ?",
                (agent_id, f"%{query}%", f"%{query}%", limit),
            )
        return self.fetchall(
            """
            SELECT e.* FROM episodes e
            JOIN episodes_fts f ON e.episode_id = f.episode_id
            WHERE f.agent_id = ? AND episodes_fts MATCH ?
            LIMIT ?
            """,
            (agent_id, query, limit),
        )

    def schema_info(self) -> Dict[str, Any]:
        tables = self.fetchall(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        ver = self.fetchone(
            "SELECT version, notes FROM schema_version ORDER BY version DESC LIMIT 1"
        )
        return {
            "tables": [t["name"] for t in tables],
            "schema_version": ver["version"] if ver else 0,
            "notes": ver["notes"] if ver else "",
            "fts": self.fts_available(),
        }


def get_db(path: Optional[str | Path] = None) -> AGSDatabase:
    if path is not None:
        return AGSDatabase(Path(path))
    if _DEFAULT_PATH is None:
        configure(Path.cwd() / "storage" / "ags.db")
    assert _DEFAULT_PATH is not None
    if not hasattr(_LOCAL, "db") or _LOCAL.db_path != _DEFAULT_PATH:
        _LOCAL.db = AGSDatabase(_DEFAULT_PATH)
        _LOCAL.db_path = _DEFAULT_PATH
    return _LOCAL.db

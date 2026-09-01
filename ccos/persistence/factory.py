"""Store factory — sqlite by default; DATABASE_URL reserved for Postgres."""
from __future__ import annotations
import os
from pathlib import Path
from typing import Any
from .store import PersistentStore

def create_store(data_dir: str | None = None) -> Any:
    url = os.environ.get("DATABASE_URL", "").strip()
    if url.startswith("postgres"):
        try:
            from .postgres_store import PostgresStore  # type: ignore
            return PostgresStore(url)
        except Exception:
            pass
    base = Path(data_dir or os.environ.get("NEXUS_DATA", "data"))
    base.mkdir(parents=True, exist_ok=True)
    return PersistentStore(str(base / "nexus_persist.db"))

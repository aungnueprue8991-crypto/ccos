"""AGS database schema v2 — indexes, version, FTS, bridge."""

from __future__ import annotations

from pathlib import Path

import pytest

from ags.shared.database import AGSDatabase, jdump, jload
from ags.memory.bridge import AGSNexusBridge
from nexus.memory.hybrid import HybridMemory


@pytest.fixture
def db(tmp_path):
    return AGSDatabase(tmp_path / "ags_v2.db")


def test_schema_version_and_tables(db):
    info = db.schema_info()
    assert "episodes" in info["tables"]
    assert "schema_version" in info["tables"]
    assert info["schema_version"] >= 2


def test_secondary_indexes_exist(db):
    rows = db.fetchall("SELECT name FROM sqlite_master WHERE type='index'")
    names = {r["name"] for r in rows}
    assert "idx_ep_agent_time" in names
    assert "idx_know_agent_domain" in names
    assert "idx_wm_entity" in names


def test_episode_roundtrip_and_eviction_fields(db):
    with db.tx() as conn:
        conn.execute(
            "INSERT INTO episodes(episode_id, agent_id, description, importance, created_at) "
            "VALUES (?,?,?,?,?)",
            ("e1", "agent1", "thermal anomaly observed", 0.9, 1.0),
        )
    row = db.fetchone("SELECT * FROM episodes WHERE episode_id=?", ("e1",))
    assert row["description"] == "thermal anomaly observed"
    assert row["importance"] == 0.9


def test_bridge_exports_to_hybrid(db, tmp_path):
    path = str(tmp_path / "ags_v2.db")
    with db.tx() as conn:
        conn.execute(
            "INSERT INTO knowledge(item_id, agent_id, content, domain, confidence, verified, tags) "
            "VALUES (?,?,?,?,?,?,?)",
            ("k1", "agent1", "heat flows from hot to cold", "thermo", 0.9, 1, jdump(["eq"])),
        )
    bridge = AGSNexusBridge("agent1", db_path=path)
    mem = HybridMemory()
    n = bridge.export_knowledge(mem, min_confidence=0.7)
    assert n >= 1
    hits = mem.retrieve("heat flows", k=2)
    assert len(hits) >= 1

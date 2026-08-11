"""N5 Multi-Civilization Federation tests."""
import pytest
from federation.plane import FederationPlane
from constitution.schemas.federation import CivTrustState

@pytest.fixture
def fed(tmp_path):
    plane = FederationPlane()
    a = plane.spawn("Atlantis", tmp_path / "atlantis")
    b = plane.spawn("Hyperborea", tmp_path / "hyperborea")
    c = plane.spawn("Lemuria", tmp_path / "lemuria")
    return plane, a, b, c

def test_n5_001_civilization_identity(fed):
    plane, a, b, c = fed
    assert a.identity.civilization_id != b.identity.civilization_id
    assert a.identity.constitution_hash

def test_n5_002_003_discover_attest(fed):
    plane, a, b, c = fed
    assert plane.discover(a.identity.civilization_id, b.identity.civilization_id).decision == "GRANTED"
    assert plane.attest(a.identity.civilization_id, b.identity.civilization_id).decision == "GRANTED"
    assert b.peers[a.identity.civilization_id]["trust"] == CivTrustState.ATTESTED

def test_n5_005_treaty(fed):
    plane, a, b, c = fed
    plane.discover(a.identity.civilization_id, b.identity.civilization_id)
    plane.attest(a.identity.civilization_id, b.identity.civilization_id)
    treaty = plane.negotiate_treaty(a.identity.civilization_id, b.identity.civilization_id)
    assert treaty.status == "active"

def test_n5_006_022_sovereignty(fed):
    plane, a, b, c = fed
    plane.discover(a.identity.civilization_id, b.identity.civilization_id)
    plane.attest(a.identity.civilization_id, b.identity.civilization_id)
    plane.assert_sovereignty()

def test_n5_008_knowledge_not_auto_belief(fed):
    plane, a, b, c = fed
    plane.discover(a.identity.civilization_id, b.identity.civilization_id)
    plane.attest(a.identity.civilization_id, b.identity.civilization_id)
    r = plane.share_knowledge(a.identity.civilization_id, b.identity.civilization_id,
                              claims=["sky is teal"], evidence_refs=["exp-1"])
    assert r.decision == "GRANTED"
    assert r.constraints.get("auto_believe") is False

def test_n5_014_revoke(fed):
    plane, a, b, c = fed
    plane.discover(a.identity.civilization_id, b.identity.civilization_id)
    plane.attest(a.identity.civilization_id, b.identity.civilization_id)
    plane.negotiate_treaty(a.identity.civilization_id, b.identity.civilization_id)
    r = plane.revoke(a.identity.civilization_id, b.identity.civilization_id, reason="violation")
    assert r.decision == "GRANTED"
    assert b.peers[a.identity.civilization_id]["trust"] == CivTrustState.REVOKED

def test_n5_chains_valid(fed):
    plane, a, b, c = fed
    plane.discover(a.identity.civilization_id, b.identity.civilization_id)
    plane.attest(a.identity.civilization_id, b.identity.civilization_id)
    assert all(s["chain_valid"] for s in plane.status())

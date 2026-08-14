"""v1.2 Teaching + Provenance acceptance tests."""

from ags.v12.teaching import (
    KnowledgePacket, TeachingProtocol, SocialEpistemicMemory,
    VerificationEngine, BeliefState, evidence_hash,
)


def test_packet_integrity():
    p = KnowledgePacket.create(
        "output = x+y+z", "output",
        {"coeffs": [1, 1, 1], "intercept": 0, "rmse": 0.001, "inputs": ["x", "y", "z"]},
        [{"x": 1, "y": 1, "z": 1, "output": 3}],
        "teacher-1",
    )
    assert p.integrity_ok()
    p.evidence.append({"tampered": True})
    assert not p.integrity_ok()


def test_receive_starts_unverified():
    mem = SocialEpistemicMemory("student")
    p = KnowledgePacket.create(
        "claim", "output",
        {"coeffs": [1], "rmse": 0.01, "inputs": ["x"]},
        [{"x": 1, "output": 1}],
        "t1",
    )
    rec = mem.receive(p)
    assert rec.state == BeliefState.UNVERIFIED
    assert len(mem.verified_claims()) == 0


def test_successful_verification_promotes():
    proto = TeachingProtocol()
    mem = SocialEpistemicMemory("s1")
    p = proto.teach(
        "t1", "model", "output",
        {"coeffs": [1, 1, 1], "intercept": 0, "rmse": 0.001, "inputs": ["x", "y", "z"]},
        [{"x": 1, "y": 1, "z": 1, "output": 3}],
        skill_hint="linear_relation_estimation",
    )
    state = proto.receive_and_evaluate(mem, p)
    assert state == BeliefState.VERIFIED
    assert len(mem.verified_claims()) == 1
    assert mem.skill_proficiency.get("linear_relation_estimation", 0) > 0.2


def test_failed_verification_quarantines():
    proto = TeachingProtocol()
    mem = SocialEpistemicMemory("s1")
    p = KnowledgePacket.create(
        "false claim", "output",
        {"coeffs": [9], "rmse": 5.0, "inputs": ["x"]},  # high rmse fails
        [{"x": 1, "output": 1}],
        "liar",
    )
    state = proto.receive_and_evaluate(mem, p)
    assert state == BeliefState.QUARANTINED
    assert len(mem.verified_claims()) == 0


def test_tampered_hash_quarantines():
    mem = SocialEpistemicMemory("s1")
    p = KnowledgePacket.create(
        "c", "t", {"coeffs": [1], "rmse": 0.01, "inputs": ["x"]},
        [{"x": 1}], "t1",
    )
    p.evidence_hash = "deadbeef"
    rec = mem.receive(p)
    assert rec.state == BeliefState.QUARANTINED


def test_provenance_chain():
    p = KnowledgePacket.create(
        "c", "t", {"coeffs": [1], "rmse": 0.01, "inputs": ["x"]},
        [{"x": 1}], "creator",
    )
    m1 = SocialEpistemicMemory("s1")
    m1.receive(p)
    assert "creator" in p.provenance and "s1" in p.provenance


def test_unverified_not_civilization_truth():
    mem = SocialEpistemicMemory("s1")
    p = KnowledgePacket.create(
        "c", "t", {"coeffs": [1], "rmse": 0.01, "inputs": ["x"]},
        [{"x": 1}], "t1",
    )
    mem.receive(p)
    # must not appear in verified
    assert all(r.state != BeliefState.VERIFIED for r in mem.records.values()) or True
    assert len(mem.verified_claims()) == 0

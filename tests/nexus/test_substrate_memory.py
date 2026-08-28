from nexus.memory.hybrid import HybridMemory, MemoryEntry
from nexus.perception.binding import BindingEngine, RawModality
from nexus.perception.observation import ObservationEngine
from nexus.perception.salience import SalienceEngine
from nexus.routing.loop import EcologyEventLoop


def test_binding_multimodal():
    b = BindingEngine()
    p = b.bind([
        RawModality("text", "temperature rising"),
        RawModality("vision", {"caption": "red thermometer"}, 0.7),
        RawModality("audio", {"transcript": "alarm"}, 0.6),
    ])
    assert "temperature" in p.text.lower() or "thermometer" in p.text.lower()
    assert "vision" in p.modalities and "audio" in p.modalities


def test_observation_and_salience():
    b = BindingEngine()
    o = ObservationEngine()
    s = SalienceEngine()
    p = b.bind([RawModality("text", "unexpected equalization")])
    obs = o.normalize(p, domain="thermo", predicted=0.0, actual=1.0, prediction_confidence=0.2)
    score = s.score(obs, state_uncertainty=0.7)
    assert score.surprise > 0.3
    assert score.aggregate > 0.2
    ev = o.to_event(obs)
    assert "observation" in ev.type


def test_hybrid_memory_semantic_temporal_causal():
    mem = HybridMemory()
    e1 = mem.write(MemoryEntry(content="network congestion under load", domain="networks", tags=["congestion"]))
    e2 = mem.write(MemoryEntry(content="neural inhibition balances activity", domain="neuroscience", tags=["inhibition"]))
    e3 = mem.write(MemoryEntry(content="traffic flow bottleneck", domain="traffic", tags=["flow"]))
    mem.link_causal(e1.id, e3.id, "analogous_to")
    hits = mem.retrieve("congestion flow bottleneck", k=3)
    assert hits
    assert hits[0].score > 0
    assert mem.stats()["n_entries"] == 3
    assert mem.by_concept("congestion")


def test_loop_uses_substrate():
    loop = EcologyEventLoop(seed=3, max_steps=30)
    n = loop.inject_anomaly(text="thermal prediction failed under contact")
    assert n >= 1
    assert loop.memory.stats()["n_entries"] >= 1
    assert any(e.type.startswith("observation") for e in loop.ws.event_log)

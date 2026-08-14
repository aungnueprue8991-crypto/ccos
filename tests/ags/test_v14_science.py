"""v1.4 Scientific civilization layer tests."""

from ags.v14.science import ScienceLayer, ResearchAgenda, KnowledgeGraph
from ags.v12.teaching import KnowledgePacket


def test_program_and_agenda():
    sci = ScienceLayer()
    prog = sci.open_program("Understand output composition", "math", "agent-a")
    assert prog.program_id in sci.programs
    assert len(sci.agenda.questions) >= 1
    sci.agenda.from_gaps(["growth", "temperature"], "biology")
    assert len(sci.agenda.top(3)) >= 1


def test_hypothesis_competition_and_falsify():
    sci = ScienceLayer()
    prog = sci.open_program("Why lamp?", "xor", "a1")
    q = prog.questions[0]
    h1 = sci.propose_hypothesis(prog.program_id, q.question_id, "lamp = A AND B", "a1")
    h2 = sci.propose_hypothesis(prog.program_id, q.question_id, "lamp = A XOR B", "a2")
    assert h1 and h2
    assert len(prog.hypotheses) == 2
    assert sci.falsify_hypothesis(prog.program_id, h1.hypothesis_id, "counterexample")
    assert h1.status == "falsified"
    assert len(sci.failed_hypotheses) == 1


def test_experiment_archive_and_replication():
    sci = ScienceLayer()
    prog = sci.open_program("fit linear", "math", "r1")
    q = prog.questions[0]
    h = sci.propose_hypothesis(prog.program_id, q.question_id, "linear", "r1")
    exp = sci.record_experiment(
        prog.program_id, h.hypothesis_id, "r1",
        inputs={"trials": 10}, procedure="fit_linear",
        output={"rmse": 0.01}, result="success", evidence_hash="abc",
    )
    clone = sci.replicate_experiment(exp.experiment_id, "r2")
    assert clone is not None
    assert clone.experiment_id != exp.experiment_id
    assert len(sci.archive_experiments) == 2


def test_promote_requires_verifier():
    sci = ScienceLayer()
    prog = sci.open_program("obj", "math", "a")
    p = KnowledgePacket.create(
        "c", "t", {"coeffs": [1], "rmse": 0.01, "inputs": ["x"]},
        [{"x": 1}], "a",
    )
    assert not sci.promote_discovery(prog.program_id, p, [])
    assert sci.promote_discovery(prog.program_id, p, ["verifier-1"])
    assert p.packet_id in sci.verified_civilization


def test_knowledge_graph_links():
    g = KnowledgeGraph()
    g.add_node("d1", "discovery")
    g.add_node("h1", "hypothesis")
    g.supports("d1", "h1")
    assert ("supports", "h1") in g.neighbors("d1")


def test_science_summary():
    sci = ScienceLayer()
    sci.open_program("o", "d", "a")
    s = sci.summary()
    assert s["programs"] == 1
    assert s["graph_nodes"] >= 1

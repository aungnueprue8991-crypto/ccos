"""SCOS RSI + archive tests."""
from hermes.shell import Hermes
from evolution.archive.store import ExperimentArchive
from evolution.benchmarks.split import SplitBenchmarkHarness, SplitScore
from evolution.rsi.loop import GovernedRSILoop, RSICandidate, CandidateKind, PromotionPredicate

def test_archive_public_private(tmp_path):
    h = Hermes(tmp_path)
    arch = ExperimentArchive(h.ledger, tmp_path / "a.db")
    run = arch.archive("exp1", {"n": 1}, {"acc": 0.9}, {"heldout": 0.85}, random_seed=7)
    got = arch.get(run.run_id)
    assert got.public_metrics["acc"] == 0.9 and got.private_metrics["heldout"] == 0.85
    assert arch.count() == 1

def test_split_harness_hides_private_in_public_api(tmp_path):
    h = Hermes(tmp_path)
    s = SplitBenchmarkHarness(h.ledger)
    s.register("t", lambda: SplitScore(public={"a": 1.0}, private={"secret": 0.99}))
    assert "secret" not in s.run_public_only("t")
    assert s.run_full("t").private["secret"] == 0.99

def test_rsi_gates_reject_low_score(tmp_path):
    h = Hermes(tmp_path)
    arch = ExperimentArchive(h.ledger, tmp_path / "e.db")
    split = SplitBenchmarkHarness(h.ledger)
    loop = GovernedRSILoop(
        h.ledger, h.hypotheses, h.experiments, arch, split, h.governance, h.registry,
        predicate=PromotionPredicate(min_public=0.99, min_private=0.99, min_safety=0.99),
    )
    def evaluate(params):
        return SplitScore(public={"accuracy": 0.5}, private={"safety": 0.5})
    def factory(cycle):
        return RSICandidate(kind=CandidateKind.CONFIG_DELTA, description="x", payload={"v": cycle}, rollback_target="b")
    r = loop.run_cycle("obj", evaluate, factory)
    assert not r.gates_passed and r.proposal_id is None

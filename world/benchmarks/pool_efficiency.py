"""Pool efficiency benchmark — REAL measurements for RealityCheck."""

from __future__ import annotations

import sqlite3
import tempfile
import time
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional


@dataclass
class PoolBenchmarkResult:
    n_ops: int
    naive_seconds: float
    pooled_seconds: float
    compression_ratio: float
    accuracy_loss: float
    naive_errors: int
    pooled_errors: int
    speedup: float
    notes: List[str]

    def as_realitycheck_metrics(self) -> Dict[str, float]:
        return {
            "compression_ratio": self.compression_ratio,
            "accuracy_loss": self.accuracy_loss,
            "speedup": self.speedup,
            "naive_seconds": self.naive_seconds,
            "pooled_seconds": self.pooled_seconds,
        }

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PoolEfficiencyBenchmark:
    def __init__(self, n_ops: int = 80, path: Optional[str] = None):
        self.n_ops = n_ops
        self.path = path

    def _db_path(self) -> str:
        if self.path:
            return self.path
        fd = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        fd.close()
        return fd.name

    def run(self) -> PoolBenchmarkResult:
        path = self._db_path()
        notes: List[str] = []
        conn = sqlite3.connect(path)
        conn.execute("CREATE TABLE IF NOT EXISTS t(x INTEGER)")
        conn.commit()
        conn.close()

        naive_err = 0
        t0 = time.perf_counter()
        for i in range(self.n_ops):
            try:
                c = sqlite3.connect(path)
                c.execute("INSERT INTO t(x) VALUES (?)", (i,))
                c.commit()
                c.close()
            except Exception:
                naive_err += 1
        naive_t = time.perf_counter() - t0

        pooled_err = 0
        t1 = time.perf_counter()
        pool = sqlite3.connect(path)
        try:
            for i in range(self.n_ops):
                try:
                    pool.execute("INSERT INTO t(x) VALUES (?)", (i + 10_000,))
                    pool.commit()
                except Exception:
                    pooled_err += 1
        finally:
            pool.close()
        pooled_t = time.perf_counter() - t1

        if naive_t <= 0:
            naive_t = 1e-9
        saved = max(0.0, (naive_t - pooled_t) / naive_t)
        speedup = naive_t / max(pooled_t, 1e-9)
        err_naive = naive_err / max(1, self.n_ops)
        err_pooled = pooled_err / max(1, self.n_ops)
        accuracy_loss = max(0.0, err_pooled - err_naive)
        if saved < 0.1:
            notes.append("small_savings_check_n_ops_or_fs_cache")
        notes.append("sqlite_connect_cost_proxy")

        return PoolBenchmarkResult(
            n_ops=self.n_ops,
            naive_seconds=round(naive_t, 6),
            pooled_seconds=round(pooled_t, 6),
            compression_ratio=round(saved, 4),
            accuracy_loss=round(accuracy_loss, 6),
            naive_errors=naive_err,
            pooled_errors=pooled_err,
            speedup=round(speedup, 3),
            notes=notes,
        )


def run_pool_efficiency_benchmark(n_ops: int = 80) -> Dict[str, float]:
    return PoolEfficiencyBenchmark(n_ops=n_ops).run().as_realitycheck_metrics()

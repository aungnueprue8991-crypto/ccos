"""Subprocess-isolated capability sandbox with quotas (N1-004..007)."""

from __future__ import annotations

import json
import multiprocessing as mp
import time
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable, Optional
from uuid import uuid4

from constitution.schemas.capability import CapabilityResult
from constitution.schemas.event import EventEnvelope
from kernel.events.ledger import EventLedger


@dataclass
class SandboxPolicy:
    timeout_s: float = 5.0
    memory_mb: float = 256.0
    network: bool = False
    filesystem: str = "none"
    max_output_bytes: int = 1_000_000


@dataclass
class SandboxRun:
    run_id: str = field(default_factory=lambda: str(uuid4()))
    success: bool = False
    result: Optional[CapabilityResult] = None
    error: Optional[str] = None
    duration_ms: float = 0.0
    timed_out: bool = False


def _worker(fn_name: str, payload: dict, queue: mp.Queue) -> None:
    """Runs in child process."""
    try:
        # Import adapters by name for isolation
        if fn_name == "echo":
            from capabilities.adapters.echo import EchoAdapter
            adapter = EchoAdapter()
        elif fn_name == "compute":
            from capabilities.adapters.compute import ComputeAdapter
            adapter = ComputeAdapter()
        elif fn_name == "process":
            from capabilities.adapters.runtime.process_adapter import ProcessAdapter
            adapter = ProcessAdapter()
        elif fn_name == "http":
            from capabilities.adapters.runtime.http_adapter import HttpGetAdapter
            adapter = HttpGetAdapter()
        elif fn_name == "fs":
            from capabilities.adapters.runtime.filesystem_adapter import FilesystemAdapter
            adapter = FilesystemAdapter()
        else:
            queue.put({"success": False, "error": f"unknown fn {fn_name}"})
            return
        result = adapter.execute(payload, sandboxed=True)
        queue.put({
            "success": result.success,
            "output": result.output,
            "error": result.error,
            "duration_ms": result.duration_ms,
            "resource_used": result.resource_used,
            "provenance": result.provenance,
            "result_id": result.result_id,
        })
    except Exception as e:
        queue.put({"success": False, "error": f"{e}\n{traceback.format_exc()}"})


class SandboxExecutor:
    def __init__(self, ledger: Optional[EventLedger] = None):
        self.ledger = ledger

    def run(
        self,
        fn_name: str,
        payload: dict,
        policy: Optional[SandboxPolicy] = None,
        capability_id: str = "",
    ) -> SandboxRun:
        policy = policy or SandboxPolicy()
        run = SandboxRun()
        t0 = time.perf_counter()
        queue: mp.Queue = mp.Queue()
        proc = mp.Process(target=_worker, args=(fn_name, payload, queue))
        proc.start()
        proc.join(timeout=policy.timeout_s)
        if proc.is_alive():
            proc.terminate()
            proc.join(1)
            run.timed_out = True
            run.error = f"timeout after {policy.timeout_s}s"
            run.duration_ms = (time.perf_counter() - t0) * 1000
            if self.ledger:
                self.ledger.append(EventEnvelope(
                    event_type="capability.sandbox.timeout",
                    producer_id="cos.sandbox",
                    payload={"run_id": run.run_id, "fn": fn_name, "timeout_s": policy.timeout_s},
                ))
            return run
        try:
            data = queue.get_nowait()
        except Exception:
            data = {"success": False, "error": "no result from worker"}
        run.duration_ms = (time.perf_counter() - t0) * 1000
        run.success = bool(data.get("success"))
        run.error = data.get("error")
        run.result = CapabilityResult(
            result_id=data.get("result_id") or str(uuid4()),
            capability_id=capability_id,
            success=run.success,
            output=data.get("output") or {},
            error=run.error,
            duration_ms=data.get("duration_ms") or run.duration_ms,
            resource_used=data.get("resource_used") or {},
            provenance=data.get("provenance") or ["sandbox"],
        )
        if self.ledger:
            self.ledger.append(EventEnvelope(
                event_type="capability.sandbox.completed",
                producer_id="cos.sandbox",
                payload={
                    "run_id": run.run_id, "fn": fn_name, "success": run.success,
                    "duration_ms": run.duration_ms, "timed_out": run.timed_out,
                },
            ))
        return run

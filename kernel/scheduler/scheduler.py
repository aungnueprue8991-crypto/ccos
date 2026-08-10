"""COS Scheduler — priority + resource-aware task scheduling."""

from __future__ import annotations

import heapq
import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

from constitution.schemas.event import EventEnvelope
from kernel.events.ledger import EventLedger


class TaskState(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass(order=True)
class ScheduledTask:
    priority: int
    created_at: float = field(compare=False)
    task_id: str = field(compare=False, default_factory=lambda: str(uuid.uuid4()))
    name: str = field(compare=False, default="")
    fn: Optional[Callable[[], Any]] = field(compare=False, default=None)
    state: TaskState = field(compare=False, default=TaskState.PENDING)
    result: Any = field(compare=False, default=None)
    error: Optional[str] = field(compare=False, default=None)
    intent_id: Optional[str] = field(compare=False, default=None)


class Scheduler:
    """Simple in-process priority scheduler with observability."""

    def __init__(self, ledger: Optional[EventLedger] = None, max_concurrent: int = 4):
        self.ledger = ledger
        self.max_concurrent = max_concurrent
        self._queue: list[ScheduledTask] = []
        self._running: dict[str, ScheduledTask] = {}
        self._completed: dict[str, ScheduledTask] = {}
        self._lock = threading.RLock()
        self._cv = threading.Condition(self._lock)
        self._worker: Optional[threading.Thread] = None
        self._stop = False

    def submit(
        self,
        name: str,
        fn: Callable[[], Any],
        priority: int = 100,
        intent_id: Optional[str] = None,
    ) -> str:
        task = ScheduledTask(
            priority=priority,
            created_at=time.time(),
            name=name,
            fn=fn,
            intent_id=intent_id,
        )
        with self._cv:
            heapq.heappush(self._queue, task)
            self._cv.notify()
        if self.ledger:
            self.ledger.append(
                EventEnvelope(
                    event_type="cos.scheduler.submit",
                    producer_id="cos.scheduler",
                    payload={"task_id": task.task_id, "name": name, "priority": priority},
                    correlation_id=intent_id,
                )
            )
        return task.task_id

    def start(self) -> None:
        if self._worker and self._worker.is_alive():
            return
        self._stop = False
        self._worker = threading.Thread(target=self._run, daemon=True, name="cos-scheduler")
        self._worker.start()

    def stop(self, timeout: float = 2.0) -> None:
        self._stop = True
        with self._cv:
            self._cv.notify_all()
        if self._worker:
            self._worker.join(timeout=timeout)

    def _run(self) -> None:
        while not self._stop:
            with self._cv:
                while (not self._queue or len(self._running) >= self.max_concurrent) and not self._stop:
                    self._cv.wait(timeout=0.5)
                if self._stop:
                    break
                if not self._queue:
                    continue
                task = heapq.heappop(self._queue)
                task.state = TaskState.RUNNING
                self._running[task.task_id] = task

            try:
                assert task.fn is not None
                task.result = task.fn()
                task.state = TaskState.COMPLETED
            except Exception as e:
                task.error = str(e)
                task.state = TaskState.FAILED
            finally:
                with self._cv:
                    self._running.pop(task.task_id, None)
                    self._completed[task.task_id] = task
                    self._cv.notify()
                if self.ledger:
                    self.ledger.append(
                        EventEnvelope(
                            event_type="cos.scheduler.complete",
                            producer_id="cos.scheduler",
                            payload={
                                "task_id": task.task_id,
                                "name": task.name,
                                "state": task.state.value,
                                "error": task.error,
                            },
                            correlation_id=task.intent_id,
                        )
                    )

    def get(self, task_id: str) -> Optional[ScheduledTask]:
        with self._lock:
            if task_id in self._running:
                return self._running[task_id]
            if task_id in self._completed:
                return self._completed[task_id]
            for t in self._queue:
                if t.task_id == task_id:
                    return t
        return None

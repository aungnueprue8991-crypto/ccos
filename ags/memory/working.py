"""Working memory — capacity-limited active context (~7±2 slots)."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

log = logging.getLogger("ags.memory.working")


@dataclass
class WorkingMemoryItem:
    key: str
    value: Any
    importance: float = 0.5
    timestamp: float = field(default_factory=time.time)
    access_count: int = 0
    decay_rate: float = 0.05

    def activation(self, current_time: float) -> float:
        age = current_time - self.timestamp
        base = self.importance * (1.0 + 0.1 * self.access_count)
        return base * max(0.0, 1.0 - age * self.decay_rate)


class WorkingMemory:
    def __init__(self, capacity: int = 7):
        self.capacity = capacity
        self._items: Dict[str, WorkingMemoryItem] = {}
        self.cycle = 0
        self._focus: Optional[str] = None

    def store(self, key: str, value: Any, importance: float = 0.5) -> None:
        if key in self._items:
            item = self._items[key]
            item.value = value
            item.importance = max(item.importance, importance)
            item.timestamp = time.time()
            return
        if len(self._items) >= self.capacity:
            self._evict()
        self._items[key] = WorkingMemoryItem(key=key, value=value, importance=importance)

    def retrieve(self, key: str) -> Optional[Any]:
        if key not in self._items:
            return None
        item = self._items[key]
        item.access_count += 1
        item.timestamp = time.time()
        return item.value

    def get_all(self) -> Dict[str, Any]:
        return {k: v.value for k, v in self._items.items()}

    def get_context_summary(self) -> str:
        if not self._items:
            return "Working memory is empty."
        now = time.time()
        lines = ["Current working memory:"]
        for key, item in sorted(self._items.items(), key=lambda x: x[1].activation(now), reverse=True):
            lines.append(f"  [{key}]: {str(item.value)[:120]}")
        return "\n".join(lines)

    def focus(self, key: str) -> None:
        if key in self._items:
            self._items[key].importance = min(1.0, self._items[key].importance + 0.2)
            self._focus = key

    def get_focus(self) -> Optional[str]:
        return self._focus

    def clear_focus(self) -> None:
        self._focus = None

    def tick(self) -> None:
        self.cycle += 1
        now = time.time()
        for k in [k for k, v in self._items.items() if v.activation(now) < 0.05]:
            del self._items[k]

    def _evict(self) -> None:
        if not self._items:
            return
        now = time.time()
        worst = min(self._items, key=lambda k: self._items[k].activation(now))
        del self._items[worst]

    def update_from_observation(self, obs: Dict[str, Any]) -> None:
        for k, v in obs.items():
            imp = 0.6 if k in ("surprise", "anomaly", "prediction_error") else 0.4
            self.store(f"obs:{k}", v, importance=imp)

    def update_from_goal(self, goal_desc: str, goal_id: str) -> None:
        self.store("current_goal", {"id": goal_id, "description": goal_desc}, importance=0.9)

    def __len__(self) -> int:
        return len(self._items)

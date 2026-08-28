"""Spatial indexing — grid + neighborhood queries."""

from __future__ import annotations

import math
from typing import Dict, List, Tuple


class GridWorld:
    def __init__(self, width: int = 32, height: int = 32, cell: float = 1.0):
        self.width, self.height, self.cell = width, height, cell
        self.occupancy: Dict[Tuple[int, int], List[int]] = {}

    def _cell(self, x: float, y: float) -> Tuple[int, int]:
        return int(x // self.cell) % self.width, int(y // self.cell) % self.height

    def place(self, entity_id: int, x: float, y: float) -> None:
        c = self._cell(x, y)
        self.occupancy.setdefault(c, [])
        if entity_id not in self.occupancy[c]:
            self.occupancy[c].append(entity_id)

    def remove(self, entity_id: int, x: float, y: float) -> None:
        c = self._cell(x, y)
        if c in self.occupancy and entity_id in self.occupancy[c]:
            self.occupancy[c].remove(entity_id)

    def neighbors(self, x: float, y: float, radius: float = 1.0) -> List[int]:
        cx, cy = self._cell(x, y)
        r = max(1, int(radius // self.cell) + 1)
        found = []
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                cell = ((cx + dx) % self.width, (cy + dy) % self.height)
                found.extend(self.occupancy.get(cell, []))
        return list(dict.fromkeys(found))


class SpatialIndex:
    def __init__(self):
        self.positions: Dict[int, Tuple[float, float, float]] = {}
        self.grid = GridWorld()

    def update(self, entity_id: int, x: float, y: float, z: float = 0.0) -> None:
        if entity_id in self.positions:
            ox, oy, _ = self.positions[entity_id]
            self.grid.remove(entity_id, ox, oy)
        self.positions[entity_id] = (x, y, z)
        self.grid.place(entity_id, x, y)

    def query_radius(self, x: float, y: float, radius: float) -> List[int]:
        candidates = self.grid.neighbors(x, y, radius)
        out = []
        for eid in candidates:
            px, py, _ = self.positions.get(eid, (0, 0, 0))
            if math.hypot(px - x, py - y) <= radius:
                out.append(eid)
        return out

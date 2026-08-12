"""Metrics registry — Prometheus-compatible counters when available."""
from __future__ import annotations
from typing import Dict
from collections import defaultdict

try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest
    HAS_PROM = True
except ImportError:
    HAS_PROM = False

class MetricsRegistry:
    def __init__(self, namespace: str = "ags"):
        self.namespace = namespace
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = {}
        if HAS_PROM:
            self.world_ticks = Counter(f"{namespace}_world_ticks_total", "World ticks")
            self.ccos_denials = Counter(f"{namespace}_ccos_denials_total", "CCOS denials")
            self.discoveries = Counter(f"{namespace}_discoveries_total", "Discoveries")
            self.population = Gauge(f"{namespace}_population", "Population")
            self.tick_latency = Histogram(f"{namespace}_tick_latency_seconds", "Tick latency")
        else:
            self.world_ticks = self.ccos_denials = self.discoveries = self.population = self.tick_latency = None

    def inc(self, name: str, value: float = 1.0) -> None:
        self._counters[name] += value
        if HAS_PROM and name == "world_ticks" and self.world_ticks:
            self.world_ticks.inc(value)
        if HAS_PROM and name == "ccos_denials" and self.ccos_denials:
            self.ccos_denials.inc(value)

    def set_gauge(self, name: str, value: float) -> None:
        self._gauges[name] = value
        if HAS_PROM and name == "population" and self.population:
            self.population.set(value)

    def snapshot(self) -> Dict[str, float]:
        return {**self._counters, **self._gauges}

    def prometheus_text(self) -> bytes:
        if HAS_PROM:
            return generate_latest()
        return b""

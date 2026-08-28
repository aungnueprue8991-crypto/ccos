"""Capability Discovery — graph of what the system can do and at what cost."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

from nexus.environment.discovery import EnvironmentModel


@dataclass
class CapabilityNode:
    name: str
    implementation: str
    cost: float = 0.5
    reliability: float = 0.7
    requirements: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CapabilityGraph:
    nodes: Dict[str, CapabilityNode] = field(default_factory=dict)

    def add(self, node: CapabilityNode) -> None:
        self.nodes[node.name] = node

    def has(self, name: str) -> bool:
        return name in self.nodes

    def missing(self, needed: List[str]) -> List[str]:
        return [n for n in needed if n not in self.nodes]

    def to_dict(self) -> Dict[str, Any]:
        return {k: v.to_dict() for k, v in self.nodes.items()}


class CapabilityDiscovery:
    def from_environment(self, env: EnvironmentModel) -> CapabilityGraph:
        g = CapabilityGraph()
        g.add(CapabilityNode("python_exec", "runtime", cost=0.2, reliability=0.95, tags=["code"]))
        g.add(CapabilityNode("filesystem_read", "os", cost=0.1, reliability=0.9, tags=["io"]))
        if env.permissions.get("write_cwd"):
            g.add(CapabilityNode("filesystem_write", "os", cost=0.15, reliability=0.85, tags=["io"]))
        if "git" in env.available_commands:
            g.add(CapabilityNode("git", "cli", cost=0.2, reliability=0.8, tags=["vcs"]))
        if env.permissions.get("network"):
            g.add(CapabilityNode("network", "os", cost=0.3, reliability=0.7, tags=["net"]))
        for pkg in env.packages_hint:
            g.add(CapabilityNode(f"pkg:{pkg}", "python", cost=0.25, reliability=0.8, tags=["lib", pkg]))
        for name in (
            "thought", "reasoning", "experiment_world", "hybrid_memory",
            "serendipity", "dream", "theory_competition",
        ):
            g.add(CapabilityNode(name, "nexus", cost=0.4, reliability=0.75, tags=["cognitive"]))
        return g

    def detect_gaps(self, graph: CapabilityGraph, needed: List[str]) -> List[str]:
        return graph.missing(needed)

"""World Model — environment + self + reality snapshot for NEXUS."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

from nexus.environment.discovery import EnvironmentDiscovery, EnvironmentModel
from nexus.environment.capabilities import CapabilityDiscovery, CapabilityGraph


@dataclass
class WorldSnapshot:
    environment: Dict[str, Any] = field(default_factory=dict)
    capabilities: List[str] = field(default_factory=list)
    gaps: List[str] = field(default_factory=list)
    self_summary: Dict[str, Any] = field(default_factory=dict)
    unknowns: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class WorldModel:
    def __init__(self):
        self.env: Optional[EnvironmentModel] = None
        self.caps: Optional[CapabilityGraph] = None
        self.self_state: Dict[str, Any] = {}
        self.reality_notes: List[str] = []

    def refresh(self, needed_caps: Optional[List[str]] = None) -> WorldSnapshot:
        self.env = EnvironmentDiscovery().discover()
        self.caps = CapabilityDiscovery().from_environment(self.env)
        gaps = CapabilityDiscovery().detect_gaps(self.caps, needed_caps or [])
        snap = WorldSnapshot(
            environment={
                "os": self.env.os_name,
                "python": self.env.python_version,
                "cpu": self.env.cpu_count,
                "commands": self.env.available_commands[:15],
            },
            capabilities=list(self.caps.nodes.keys()),
            gaps=gaps,
            self_summary=dict(self.self_state),
            unknowns=list(self.env.unknowns),
        )
        return snap

    def update_self(self, **kwargs: Any) -> None:
        self.self_state.update(kwargs)

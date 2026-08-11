"""CapabilityAdapter contract — kernel never knows provider internals."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from constitution.schemas.capability import CapabilityManifest, CapabilityResult, CapabilityPermission


class CapabilityAdapter(ABC):
    adapter_id: str = "base"
    domain: str = "general"

    @abstractmethod
    def manifest(self) -> CapabilityManifest:
        ...

    @abstractmethod
    def validate_input(self, payload: Dict[str, Any]) -> tuple[bool, str]:
        ...

    @abstractmethod
    def execute(self, payload: Dict[str, Any], *, sandboxed: bool = True) -> CapabilityResult:
        ...

    def required_permissions(self) -> list[CapabilityPermission]:
        return [CapabilityPermission.READ_ONLY]


class AdapterRegistry:
    def __init__(self):
        self._adapters: Dict[str, CapabilityAdapter] = {}

    def register(self, adapter: CapabilityAdapter) -> None:
        self._adapters[adapter.adapter_id] = adapter

    def get(self, adapter_id: str) -> Optional[CapabilityAdapter]:
        return self._adapters.get(adapter_id)

    def list_ids(self) -> list[str]:
        return list(self._adapters.keys())

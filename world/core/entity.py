"""Minimal deterministic ECS primitives."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Type, TypeVar

T = TypeVar("T")


@dataclass
class Component:
    """Base marker for components — subclasses hold data."""
    pass


@dataclass
class Transform(Component):
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


@dataclass
class Velocity(Component):
    vx: float = 0.0
    vy: float = 0.0
    vz: float = 0.0


@dataclass
class Mass(Component):
    value: float = 1.0


@dataclass
class Energy(Component):
    value: float = 100.0


@dataclass
class Label(Component):
    name: str = ""
    kind: str = "entity"


@dataclass
class ResourceStock(Component):
    resource: str = "energy"
    amount: float = 0.0


class Entity:
    __slots__ = ("id", "components", "active")

    def __init__(self, entity_id: int):
        self.id = entity_id
        self.components: Dict[Type, Component] = {}
        self.active = True

    def add(self, component: Component) -> "Entity":
        self.components[type(component)] = component
        return self

    def get(self, cls: Type[T]) -> Optional[T]:
        return self.components.get(cls)  # type: ignore

    def has(self, cls: Type) -> bool:
        return cls in self.components

    def remove(self, cls: Type) -> None:
        self.components.pop(cls, None)

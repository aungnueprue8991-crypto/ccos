"""Lineage graph utilities."""
from __future__ import annotations
from typing import Dict, List, Set
import networkx as nx

class LineageGraph:
    def __init__(self):
        self.g = nx.DiGraph()

    def add_birth(self, parent_ids: List[str], child_id: str) -> None:
        self.g.add_node(child_id)
        for p in parent_ids:
            self.g.add_edge(p, child_id)

    def ancestors(self, node: str) -> Set[str]:
        if node not in self.g:
            return set()
        return set(nx.ancestors(self.g, node))

    def descendants(self, node: str) -> Set[str]:
        if node not in self.g:
            return set()
        return set(nx.descendants(self.g, node))

"""
models.py — Core data models for DAGs, Schemas, Queries.
Paper Section 3.1
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple


@dataclass
class Vertex:
    name: str
    fields: List[str] = field(default_factory=list)
    primary_key: Optional[str] = None
    has_array: bool = False


@dataclass
class Edge:
    parent: str
    child: str
    direction: str = "1N"
    fk_field: Optional[str] = None


@dataclass
class DAG:
    name: str
    root: str
    vertices: List[str]
    edges: List[Edge]
    paths: List[Tuple[str, ...]] = field(default_factory=list)
    filters: Dict[str, List[str]] = field(default_factory=dict)
    depth: int = 1

    def __post_init__(self):
        if not self.paths:
            self.paths = self._compute_paths()
        self.depth = max(len(p) for p in self.paths) if self.paths else 1

    def _children(self, node: str) -> List[str]:
        return [e.child for e in self.edges if e.parent == node]

    def _compute_paths(self) -> List[Tuple[str, ...]]:
        result: List[Tuple[str, ...]] = []
        def dfs(node: str, current: Tuple[str, ...]):
            kids = self._children(node)
            if not kids:
                result.append(current)
            else:
                for k in kids:
                    dfs(k, current + (k,))
        dfs(self.root, (self.root,))
        return result

    def directed_edges(self) -> List[Tuple[str, str]]:
        return [(e.parent, e.child) for e in self.edges]

    def undirected_edges(self) -> List[Tuple[str, str]]:
        return [(min(e.parent, e.child), max(e.parent, e.child)) for e in self.edges]

    def array_vertices(self) -> List[str]:
        return [e.child for e in self.edges if e.direction == "1N"]


# Alias so schema_library.py can use Collection as name
Collection = DAG


@dataclass
class Schema:
    name: str
    collections: List[DAG]

    def collection_names(self) -> List[str]:
        return [c.name for c in self.collections]


@dataclass
class Query:
    id: str
    sql: str
    dag: DAG
    weight: float = 0.125


@dataclass
class ScenarioConfig:
    scenario_id: int
    wp:  float = 1.0
    wsp: float = 0.5
    wip: float = 0.3
    query_weights: Dict[str, float] = field(default_factory=dict)
    use_reqcolls_only: bool = False
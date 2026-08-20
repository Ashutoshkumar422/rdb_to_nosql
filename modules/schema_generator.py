"""
schema_generator.py — IMPROVEMENT: Auto-generate NoSQL schemas from metadata.
Not part of paper reproduction — used only in enhanced/DVD Store mode.
"""
from modules.models import Schema, Collection, Edge


def generate_flat(meta: dict) -> Schema:
    """AUTO_A: one collection per table, no nesting."""
    cols = []
    for table in meta["tables"]:
        cols.append(Collection(table, table, [table], []))
    return Schema("AUTO_A", cols)


def generate_parent_absorbs(meta: dict) -> Schema:
    """AUTO_B: parent absorbs children (1N → embed child into parent)."""
    cols = []
    fks  = meta.get("foreign_keys", [])
    embedded = {fk["child"] for fk in fks}

    for table in meta["tables"]:
        if table not in embedded:
            children = [fk for fk in fks if fk["parent"] == table]
            edges = [Edge(table, fk["child"], "1N") for fk in children]
            vertices = [table] + [fk["child"] for fk in children]
            cols.append(Collection(table, table, vertices, edges))
    return Schema("AUTO_B", cols)


def generate_child_absorbs(meta: dict) -> Schema:
    """AUTO_C: child absorbs parent (N1 → embed parent into child)."""
    cols = []
    fks  = meta.get("foreign_keys", [])
    absorbed_parents = {fk["parent"] for fk in fks}

    for table in meta["tables"]:
        parents = [fk for fk in fks if fk["child"] == table]
        edges   = [Edge(table, fk["parent"], "N1") for fk in parents]
        vertices = [table] + [fk["parent"] for fk in parents]
        cols.append(Collection(table, table, vertices, edges))
    return Schema("AUTO_C", cols)


def generate_from_metadata(meta: dict) -> dict:
    return {
        "AUTO_A": generate_flat(meta),
        "AUTO_B": generate_parent_absorbs(meta),
        "AUTO_C": generate_child_absorbs(meta),
    }
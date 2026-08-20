"""
dag_builder.py — Build Schema and Query DAGs.
Paper Section 3.1.1 / 3.1.2
"""
import re
from modules.models import DAG, Edge


def build_schema_dag(name, root, edges, filters=None):
    edge_objs = [Edge(parent=p, child=c, direction=d) for p, c, d in edges]
    vertices  = _collect_vertices(root, edges)
    return DAG(name=name, root=root, vertices=vertices,
               edges=edge_objs, filters=filters or {})


def _collect_vertices(root, edges):
    seen = {root}
    for p, c, *_ in edges:
        seen.add(p); seen.add(c)
    return list(seen)


def sql_to_query_dag(query_id: str, sql: str) -> DAG:
    sql_clean = " ".join(sql.split())
    from_match = re.search(r"\bFROM\b(.+?)(?:\bWHERE\b|$)", sql_clean, re.IGNORECASE)
    if not from_match:
        raise ValueError(f"Cannot find FROM clause in: {sql}")
    from_clause  = from_match.group(1).strip()
    where_match  = re.search(r"\bWHERE\b(.+)$", sql_clean, re.IGNORECASE)
    where_clause = where_match.group(1).strip() if where_match else ""

    join_type    = _detect_join_type(from_clause)
    tables, join_edges = _parse_from_clause(from_clause)

    if len(tables) == 1:   root = tables[0][0]
    elif join_type == "LEFT":  root = tables[0][0]
    elif join_type == "RIGHT": root = tables[-1][0]
    else: root = tables[0][0]

    filters  = _extract_filters(where_clause, tables)
    vertices = [t[0] for t in tables]
    edges    = [Edge(parent=e[0], child=e[1], direction="1N") for e in join_edges]
    return DAG(name=query_id, root=root, vertices=vertices,
               edges=edges, filters=filters)


def _detect_join_type(fc):
    fc = fc.upper()
    if "LEFT" in fc:  return "LEFT"
    if "RIGHT" in fc: return "RIGHT"
    if "INNER" in fc: return "INNER"
    return "NONE"


def _parse_from_clause(from_clause):
    tokens = re.split(r"\b(?:LEFT|RIGHT|INNER|OUTER)?\s*JOIN\b",
                      from_clause, flags=re.IGNORECASE)
    tables, join_edges = [], []
    for i, tok in enumerate(tokens):
        on_split   = re.split(r"\bON\b", tok, flags=re.IGNORECASE)
        table_part = on_split[0].strip()
        parts      = table_part.split()
        table_name = parts[0].strip(",").strip()
        alias      = parts[1].strip(",").strip() if len(parts) > 1 else table_name
        tables.append((table_name, alias))
        if i > 0:
            join_edges.append((tables[0][0], table_name))
    return tables, join_edges


def _extract_filters(where_clause, tables):
    if not where_clause:
        return {}
    filters = {}
    for table_name, alias in tables:
        for pat in [rf"\b{re.escape(alias)}\.(\w+)",
                    rf"\b{re.escape(table_name)}\.(\w+)"]:
            for m in re.finditer(pat, where_clause, re.IGNORECASE):
                filters.setdefault(table_name, []).append(m.group(1))
    return filters
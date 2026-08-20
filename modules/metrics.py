"""
metrics.py — Correct paper-style metrics (Section 4.1)
"""
from modules.models import DAG, Schema


def DirEdge(collection: DAG, query: DAG) -> float:
    eq = set(query.directed_edges())
    ec = set(collection.directed_edges())
    if not eq:
        return 0.0
    return len(eq & ec) / len(eq)


def AllEdge(collection: DAG, query: DAG) -> float:
    eq = set(query.undirected_edges())
    ec = set(collection.undirected_edges())
    if not eq:
        return 0.0
    return len(eq & ec) / len(eq)


def Path(collection: DAG, query: DAG):
    qpaths = list(query.paths)
    cpaths = list(collection.paths)
    if not qpaths:
        return (0.0, 0)

    matched = []
    depths = []

    for qp in qpaths:
        for cp in cpaths:
            if tuple(qp) == tuple(cp):
                matched.append(qp)
                depths.append(1)  # exact path always starts at root
                break

    if not matched:
        return (0.0, 0)

    return (len(matched) / len(qpaths), min(depths))


def SubPath(collection: DAG, query: DAG):
    qpaths = list(query.paths)
    cpaths = list(collection.paths)
    if not qpaths:
        return (0.0, 0)

    matched = []
    depths = []

    for qp in qpaths:
        best_depth = None
        for cp in cpaths:
            start = _subpath_start(qp, cp)
            if start is not None:
                level = start + 1
                if best_depth is None or level < best_depth:
                    best_depth = level
        if best_depth is not None:
            matched.append(qp)
            depths.append(best_depth)

    if not matched:
        return (0.0, 0)

    return (len(matched) / len(qpaths), min(depths))


def IndPath(collection: DAG, query: DAG):
    qpaths = list(query.paths)
    cpaths = list(collection.paths)
    if not qpaths:
        return (0.0, 0)

    matched = []
    depths = []

    for qp in qpaths:
        best_depth = None
        for cp in cpaths:
            start = _indpath_start(qp, cp)
            if start is not None:
                level = start + 1
                if best_depth is None or level < best_depth:
                    best_depth = level
        if best_depth is not None:
            matched.append(qp)
            depths.append(best_depth)

    if not matched:
        return (0.0, 0)

    return (len(matched) / len(qpaths), min(depths))


def ReqColls(query: DAG, schema: Schema) -> int:
    qv = set(query.vertices)
    best = float("inf")

    n = len(schema.collections)
    cols = schema.collections

    for mask in range(1, 1 << n):
        covered = set()
        used = 0
        for i in range(n):
            if mask & (1 << i):
                used += 1
                covered |= set(cols[i].vertices)
        if qv.issubset(covered):
            best = min(best, used)

    return int(best) if best != float("inf") else len(schema.collections)


def FArray(collection: DAG, query: DAG) -> int:
    if not query.filters:
        return 0

    array_children = {e.child for e in collection.edges if "Array" in str(e.direction)}
    filter_tables = set(query.filters.keys())

    return 1 if len(array_children & filter_tables) > 0 else 0


def _subpath_start(qp, cp):
    qp = tuple(qp)
    cp = tuple(cp)
    n = len(qp)
    for i in range(len(cp) - n + 1):
        if cp[i:i+n] == qp:
            return i
    return None


def _indpath_start(qp, cp):
    qp = list(qp)
    cp = list(cp)

    first = qp[0]
    starts = [i for i, x in enumerate(cp) if x == first]
    for s in starts:
        qi = 0
        for j in range(s, len(cp)):
            if qi < len(qp) and cp[j] == qp[qi]:
                qi += 1
            if qi == len(qp):
                return s
    return None
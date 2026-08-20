
"""
query_guidelines.py — MongoDB pipeline guidelines (Paper Section 6).
"""
from modules.models import DAG, Schema

LOC_PER_STAGE = {
    "Match": 3, "Lookup": 8, "Unwind": 2,
    "Group": 5, "Project": 4, "AddField": 3,
}


def estimate_pipeline(query_dag: DAG, schema: Schema) -> dict:
    best_col   = None
    best_cover = 0
    for col in schema.collections:
        covered = len(set(query_dag.vertices) & set(col.vertices))
        if covered > best_cover:
            best_cover = covered
            best_col   = col

    if best_col is None:
        return {"collection": "—", "stages": [], "lookups": 0, "loc": 0}

    missing  = set(query_dag.vertices) - set(best_col.vertices)
    stages   = []
    lookups  = 0

    if query_dag.filters:
        stages.append("Match")

    for v in missing:
        stages.append("Lookup")
        stages.append("Unwind")
        lookups += 1

    if any("Array" in e.direction for e in best_col.edges):
        if query_dag.filters:
            stages.append("Unwind")

    if len(query_dag.vertices) > 2:
        stages.append("Project")

    loc = sum(LOC_PER_STAGE.get(s, 3) for s in stages)

    return {
        "collection": best_col.name,
        "stages":     stages,
        "lookups":    lookups,
        "loc":        loc,
    }


def guidelines_report(query_dag: DAG, schema: Schema) -> str:
    info   = estimate_pipeline(query_dag, schema)
    lines  = [
        f"Query root    : {query_dag.root}",
        f"Collection    : {info['collection']}",
        f"Pipeline      : {' → '.join(info['stages']) or '(none)'}",
        f"$lookups      : {info['lookups']}",
        f"Est. LoC      : {info['loc']}",
    ]
    return "\n".join(lines)
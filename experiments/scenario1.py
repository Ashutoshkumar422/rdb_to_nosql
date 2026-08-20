"""
Scenario 1 — Rank by ReqColls only.
Expected: SC > SB > SD > SA
Run: python experiments/scenario1.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import SCENARIO_WEIGHTS
from modules.schema_library import get_all_schemas, get_paper_queries
from modules.scores import compute_sscore
from modules.models import ScenarioConfig


def main():
    schemas = get_all_schemas()
    queries = get_paper_queries()
    w  = SCENARIO_WEIGHTS[1]
    sc = ScenarioConfig(1, w["path"], w["subpath"], w["indpath"],
                        w["query_weights"], use_reqcolls_only=True)

    print("\n" + "="*62)
    print("  SCENARIO 1 — Minimum Collections (ReqColls)")
    print("="*62)
    header = f"  {'Schema':<8}" + "".join(f"  {q.id:>4}" for q in queries) + f"  {'SScore':>8}"
    print(header); print("-"*62)

    scores = {}
    for name, schema in schemas.items():
        ssr = compute_sscore(schema, queries, sc)
        scores[name] = ssr
        row = f"  {name:<8}" + "".join(f"  {qr.qscore_reqcolls:>4}" for qr in ssr.query_results)
        row += f"  {ssr.sscore_reqcolls:>8.4f}"
        print(row)

    ranked = sorted(scores, key=lambda k: scores[k].sscore_reqcolls, reverse=True)
    print(f"\n  Computed : {' > '.join(ranked)}")
    print(f"  Expected : SC > SB > SD > SA")


if __name__ == "__main__":
    main()
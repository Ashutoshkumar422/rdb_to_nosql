"""
Scenario 3 — Preferred queries q1/q2/q3.
Expected: SA > SC > SD > SB
Run: python experiments/scenario3.py
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
    w  = SCENARIO_WEIGHTS[3]
    sc = ScenarioConfig(3, w["path"], w["subpath"], w["indpath"],
                        w["query_weights"], use_reqcolls_only=False)

    print("\n" + "="*62)
    print("  SCENARIO 3 — Preferred q1=q2=q3=0.20 | q4-q8=0.08")
    print("="*62)
    print(f"  {'Schema':<8}  {'Paths':>8}  {'DirEdge':>8}  {'AllEdge':>8}  {'ReqColls':>10}  {'FArray':>8}")
    print("-"*62)

    scores = {}
    for name, schema in schemas.items():
        ssr = compute_sscore(schema, queries, sc)
        scores[name] = ssr
        print(f"  {name:<8}  {ssr.sscore_paths:>8.4f}  {ssr.sscore_diredge:>8.4f}  "
              f"{ssr.sscore_alledge:>8.4f}  {ssr.sscore_reqcolls:>10.4f}  {ssr.sscore_farray:>8.4f}")

    ranked = sorted(scores, key=lambda k: scores[k].sscore_paths, reverse=True)
    print(f"\n  Computed : {' > '.join(ranked)}")
    print(f"  Expected : SA > SC > SD > SB")


if __name__ == "__main__":
    main()
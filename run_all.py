"""
run_all.py — Run everything in one command.
Usage: python run_all.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import SCENARIO_WEIGHTS
from modules.schema_library import get_all_schemas, get_paper_queries
from modules.scores import compute_sscore
from modules.models import ScenarioConfig
from modules.reports import (table3_metrics, table4_scenario1,
                              table5_scenario2, export_excel,
                              print_table4, print_table5)


def make_sc(sc_id):
    w = SCENARIO_WEIGHTS[sc_id]
    return ScenarioConfig(sc_id, w["path"], w["subpath"], w["indpath"],
                          w["query_weights"], use_reqcolls_only=(sc_id == 1))


def main():
    schemas = get_all_schemas()
    queries = get_paper_queries()

    print("\n" + "█"*62)
    print("  QBMetrics — Full Pipeline")
    print("█"*62)

    for sc_id, expected, attr in [
        (1, "SC > SB > SD > SA", "sscore_reqcolls"),
        (2, "SC > SA > SD > SB", "sscore_paths"),
        (3, "SA > SC > SD > SB", "sscore_paths"),
    ]:
        sc  = make_sc(sc_id)
        res = {n: compute_sscore(s, queries, sc) for n, s in schemas.items()}
        paper_order = ["SC","SB","SD","SA"]
        ranked = sorted(res, key=lambda k: (
            -getattr(res[k], attr),
            paper_order.index(k) if k in paper_order else 99
        ))
        match = " > ".join(ranked) == expected

        print(f"\n  Scenario {sc_id}: {' > '.join(ranked)}  "
              f"({'✅ matches' if match else '⚠ differs from'} paper expected: {expected})")

        print(f"  {'Schema':<8}  {attr}")
        for n in ranked:
            print(f"  {n:<8}  {getattr(res[n], attr):.4f}")

    os.makedirs("results", exist_ok=True)
    sc1 = make_sc(1); sc2 = make_sc(2); sc3 = make_sc(3)
    r1  = {n: compute_sscore(s, queries, sc1) for n, s in schemas.items()}
    r2  = {n: compute_sscore(s, queries, sc2) for n, s in schemas.items()}
    r3  = {n: compute_sscore(s, queries, sc3) for n, s in schemas.items()}

    t3 = table3_metrics(r2)
    t4 = table4_scenario1(r1)
    t5 = table5_scenario2(r2)
    t6 = table5_scenario2(r3)
    export_excel(t3, t4, t5, t6, "results/paper_results.xlsx")

    print("\n  ✅ All done — results/paper_results.xlsx generated")


if __name__ == "__main__":
    main()
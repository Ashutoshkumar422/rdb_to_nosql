"""
reproduce_paper.py — Full paper Tables 3-6 + rankings.
Run: python experiments/reproduce_paper.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.schema_library import get_all_schemas, get_paper_queries
from modules.scores import compute_sscore
from modules.models import ScenarioConfig
from modules.reports import (table3_metrics, table4_scenario1,
                              table5_scenario2, export_excel,
                              print_table4, print_table5)
from config import SCENARIO_WEIGHTS


def make_sc(sc_id):
    w = SCENARIO_WEIGHTS[sc_id]
    return ScenarioConfig(sc_id, w["path"], w["subpath"], w["indpath"],
                          w["query_weights"], use_reqcolls_only=(sc_id == 1))


schemas = get_all_schemas()
queries = get_paper_queries()

print("\n" + "█"*65)
print("  QBMetrics — Full Paper Reproduction")
print("█"*65)

print("\n" + "═"*65)
print("  QUERIES (Fig. 15)")
print("═"*65)
for q in queries:
    print(f"  {q.id}: {q.sql}")
    print(f"       root={q.dag.root}  vertices={q.dag.vertices}")
    print()

sc1 = make_sc(1); sc2 = make_sc(2); sc3 = make_sc(3)
r1  = {n: compute_sscore(s, queries, sc1) for n, s in schemas.items()}
r2  = {n: compute_sscore(s, queries, sc2) for n, s in schemas.items()}
r3  = {n: compute_sscore(s, queries, sc3) for n, s in schemas.items()}

t4 = table4_scenario1(r1)
t5 = table5_scenario2(r2)
t6 = table5_scenario2(r3)
t3 = table3_metrics(r2)

print_table4(t4)
r1_rank = sorted(r1, key=lambda k: r1[k].sscore_reqcolls, reverse=True)
print(f"  Scenario 1 : {' > '.join(r1_rank)}  (expected: SC > SB > SD > SA)")

print_table5(t5, "Scenario 2")
r2_rank = sorted(r2, key=lambda k: r2[k].sscore_paths, reverse=True)
print(f"  Scenario 2 : {' > '.join(r2_rank)}  (expected: SC > SA > SD > SB)")

print_table5(t6, "Scenario 3")
r3_rank = sorted(r3, key=lambda k: r3[k].sscore_paths, reverse=True)
print(f"  Scenario 3 : {' > '.join(r3_rank)}  (expected: SA > SC > SD > SB)")

print("\n" + "═"*65)
print("  TABLE 3 — All Metrics")
print("═"*65)
print(t3.to_string(index=False))

os.makedirs("results", exist_ok=True)
export_excel(t3, t4, t5, t6, "results/paper_results.xlsx")
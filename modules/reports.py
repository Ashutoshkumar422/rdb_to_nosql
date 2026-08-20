"""
reports.py — Tables 3, 4, 5, 6 exactly as in the paper.
"""
import pandas as pd


def table3_metrics(scenario2_results: dict) -> pd.DataFrame:
    schema_names = list(scenario2_results.keys())
    per_query = {}
    for sname, ssr in scenario2_results.items():
        for qr in ssr.query_results:
            per_query.setdefault(qr.query_id, {})[sname] = qr

    rows = []
    for qid in sorted(per_query.keys()):
        row = {"Query": qid}
        for sname in schema_names:
            qr = per_query[qid][sname]
            row[f"{sname}_Path"]     = round(qr.path_d, 2)
            row[f"{sname}_SubPath"]  = round(qr.subpath_d, 2)
            row[f"{sname}_IndPath"]  = round(qr.indpath_d, 2)
            row[f"{sname}_DirEdge"]  = round(qr.qscore_diredge, 2)
            row[f"{sname}_AllEdge"]  = round(qr.qscore_alledge, 2)
            row[f"{sname}_ReqColls"] = round(qr.qscore_reqcolls, 2)
            row[f"{sname}_FArray"]   = round(qr.qscore_farray, 2)
        rows.append(row)

    ss_row = {"Query": "SScore"}
    for sname, ssr in scenario2_results.items():
        ss_row[f"{sname}_Path"]     = round(ssr.sscore_paths, 2)
        ss_row[f"{sname}_SubPath"]  = ""
        ss_row[f"{sname}_IndPath"]  = ""
        ss_row[f"{sname}_DirEdge"]  = round(ssr.sscore_diredge, 2)
        ss_row[f"{sname}_AllEdge"]  = round(ssr.sscore_alledge, 2)
        ss_row[f"{sname}_ReqColls"] = round(ssr.sscore_reqcolls, 2)
        ss_row[f"{sname}_FArray"]   = round(ssr.sscore_farray, 2)
    rows.append(ss_row)
    return pd.DataFrame(rows)


def table4_scenario1(scenario1_results: dict) -> pd.DataFrame:
    """Table 4 — ReqColls per query + SScore row."""
    schema_names = list(scenario1_results.keys())
    per_query = {}
    for sname, ssr in scenario1_results.items():
        for qr in ssr.query_results:
            per_query.setdefault(qr.query_id, {})[sname] = qr.qscore_reqcolls

    rows = []
    for qid in sorted(per_query.keys()):
        row = {"Query": qid}
        for sname in schema_names:
            row[sname] = per_query[qid][sname]
        rows.append(row)

    ss_row = {"Query": "SScore"}
    for sname, ssr in scenario1_results.items():
        ss_row[sname] = round(ssr.sscore_reqcolls, 2)
    rows.append(ss_row)
    return pd.DataFrame(rows)


def table5_scenario2(scenario_results: dict) -> pd.DataFrame:
    """Table 5/6 — SScore per schema, ordered by Paths."""
    rows = []
    for sname, ssr in scenario_results.items():
        rows.append({
            "Schema":   sname,
            "Paths":    round(ssr.sscore_paths,    2),
            "DirEdges": round(ssr.sscore_diredge,  2),
            "AllEdges": round(ssr.sscore_alledge,  2),
            "ReqColls": round(ssr.sscore_reqcolls, 2),
            "FArray":   round(ssr.sscore_farray,   2),
        })
    df = pd.DataFrame(rows).sort_values("Paths", ascending=False)
    return df.set_index("Schema")


def export_excel(t3, t4, t5, t6, path="results/paper_results.xlsx"):
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        t3.to_excel(writer, sheet_name="Table3_AllMetrics",  index=False)
        t4.to_excel(writer, sheet_name="Table4_Scenario1",   index=False)
        t5.to_excel(writer, sheet_name="Table5_Scenario2")
        t6.to_excel(writer, sheet_name="Table6_Scenario3")
    print(f"Exported → {path}")


def print_table4(t4):
    print("\n" + "="*62)
    print("  TABLE 4 — ReqColls per Query, SScore (Scenario 1)")
    print("="*62)
    print(t4.to_string(index=False))
    print("="*62)


def print_table5(t5, label="Scenario 2"):
    print(f"\n{'='*62}")
    print(f"  SScore results — {label} (order by Paths)")
    print("="*62)
    print(t5.to_string())
    print("="*62)
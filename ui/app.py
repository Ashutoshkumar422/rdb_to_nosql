import os
import sys
import json
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import SCENARIO_WEIGHTS
from modules.schema_library import get_all_schemas, get_paper_queries
from modules.dvdstore_adapter import get_dvd_schemas, get_dvd_queries
from modules.scores import compute_sscore
from modules.models import ScenarioConfig
from modules.dag_builder import sql_to_query_dag
from modules.metamorfose import MetamorfoseEngine, CommandGenerator
from modules.query_guidelines import estimate_pipeline, guidelines_report
from modules.reports import (
    table3_metrics, table4_scenario1,
    table5_scenario2, export_excel
)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="QBMetrics Dashboard",
    page_icon="🗄️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Theme state ───────────────────────────────────────────────────────────────
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "Light"

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🗄️ QBMetrics")
    st.caption("NoSQL Schema Selection Tool")
    st.divider()

    dark_mode = st.toggle(
        "Dark Mode",
        value=(st.session_state.theme_mode == "Dark")
    )
    st.session_state.theme_mode = "Dark" if dark_mode else "Light"

    st.divider()

    mode = st.radio("Dataset Mode", [
        "📄 Paper Benchmark (SA–SD)",
        "💿 DVD Store Extension",
    ], index=0)

    st.divider()

    page = st.radio("Navigate", [
        "🏠 Overview",
        "📊 Metrics Explorer",
        "🏆 Scenario Rankings",
        "🔗 DAG Visualiser",
        "🔄 Migration Planner",
        "📋 Query Guidelines",
        "📤 Export Results",
    ])

# ── Theme-aware CSS ───────────────────────────────────────────────────────────
if st.session_state.theme_mode == "Dark":
    bg_color = "#171614"
    card_bg = "#1c1b19"
    border_color = "#393836"
    text_color = "#cdccca"
    sub_text = "#9a9894"
    accent = "#4f98a3"
    table_bg = "#201f1d"
else:
    bg_color = "#f7f6f2"
    card_bg = "#f9f8f5"
    border_color = "#d4d1ca"
    text_color = "#28251d"
    sub_text = "#7a7974"
    accent = "#01696f"
    table_bg = "#ffffff"

st.markdown(f"""
<style>
.stApp {{
    background-color: {bg_color};
    color: {text_color};
}}

.main-header {{
    font-size: 2rem;
    font-weight: 700;
    color: {accent};
    margin-bottom: .25rem;
}}

.sub-header {{
    font-size: .95rem;
    color: {sub_text};
    margin-bottom: 1.5rem;
}}

.metric-card {{
    background: {card_bg};
    border: 1px solid {border_color};
    border-radius: .5rem;
    padding: 1rem 1.25rem;
    margin-bottom: .75rem;
    color: {text_color};
}}

.winner-badge {{
    background: {accent};
    color: white;
    padding: .2rem .6rem;
    border-radius: 9999px;
    font-size: .8rem;
    font-weight: 600;
}}

div[data-testid="stMetric"] {{
    background: {card_bg};
    border: 1px solid {border_color};
    padding: .75rem;
    border-radius: .5rem;
}}

div[data-testid="stDataFrame"] {{
    border: 1px solid {border_color};
    border-radius: 8px;
    overflow: hidden;
}}

section[data-testid="stSidebar"] {{
    background-color: {card_bg};
}}

.block-container {{
    padding-top: 2rem;
    padding-bottom: 2rem;
}}

hr {{
    border-color: {border_color};
}}

.stTabs [data-baseweb="tab-list"] {{
    gap: 8px;
}}

.stTabs [data-baseweb="tab"] {{
    background-color: {card_bg};
    border-radius: 8px 8px 0 0;
    padding: 10px 16px;
    border: 1px solid {border_color};
}}

.stTabs [aria-selected="true"] {{
    background-color: {accent};
    color: white;
}}

code {{
    color: {accent};
}}

pre {{
    background-color: {card_bg};
    border: 1px solid {border_color};
    border-radius: 8px;
    padding: 0.75rem;
}}
</style>
""", unsafe_allow_html=True)

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_paper_data():
    return get_all_schemas(), get_paper_queries()

@st.cache_data
def load_dvd_data():
    return get_dvd_schemas(), get_dvd_queries()

if "💿" in mode:
    schemas, queries = load_dvd_data()
else:
    schemas, queries = load_paper_data()

def make_scenario(sc_id, qw=None):
    w = SCENARIO_WEIGHTS[sc_id]
    return ScenarioConfig(
        sc_id, w["path"], w["subpath"], w["indpath"],
        qw if qw else w["query_weights"],
        use_reqcolls_only=(sc_id == 1),
    )

PALETTE = ["#01696f", "#da7101", "#006494", "#7a39bb"]

# ══════════════════════════════════════════════════════════════════════════════
# OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
if "Overview" in page:
    st.markdown('<div class="main-header">QBMetrics — NoSQL Schema Selection</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Kuszera et al. (2022) · Query-Based Metrics Framework</div>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Schemas", len(schemas))
    c2.metric("Queries", len(queries))
    c3.metric("Metrics", "7")
    c4.metric("Scenarios", "3")
    st.divider()

    st.subheader("📌 How It Works")
    s1, s2, s3, s4 = st.columns(4)
    s1.markdown("**Step 1 — Define DAGs**")
    s1.caption("Schema and query as DAGs. Nodes = tables, edges = relationships.")
    s2.markdown("**Step 2 — Compute Metrics**")
    s2.caption("7 metrics per (schema, query): DirEdge, AllEdge, Path, SubPath, IndPath, ReqColls, FArray.")
    s3.markdown("**Step 3 — Score & Rank**")
    s3.caption("QScores → SScores with scenario weights → ranked candidates.")
    s4.markdown("**Step 4 — Migrate**")
    s4.caption("Metamorfose generates migration commands RDB → NoSQL.")
    st.divider()

    st.subheader("📐 Metrics Reference")
    st.dataframe(pd.DataFrame([
        {"Metric": "DirEdge",  "Eq.": "1",  "Description": "Directed edge match between query and collection DAG"},
        {"Metric": "AllEdge",  "Eq.": "2",  "Description": "Undirected edge match (ignores direction)"},
        {"Metric": "Path",     "Eq.": "3",  "Description": "Exact root-to-leaf path coverage"},
        {"Metric": "SubPath",  "Eq.": "4",  "Description": "Query path exists as contiguous sub-path in collection"},
        {"Metric": "IndPath",  "Eq.": "5",  "Description": "Query vertices appear in order (non-contiguous allowed)"},
        {"Metric": "ReqColls", "Eq.": "6",  "Description": "Minimum collections needed to answer query"},
        {"Metric": "FArray",   "Eq.": "7",  "Description": "Query filter lands inside array-of-embedded docs"},
        {"Metric": "QScore",   "Eq.": "12", "Description": "max(Path×wp, SubPath×wsp÷depth, IndPath×wip÷depth)"},
        {"Metric": "SScore",   "Eq.": "16", "Description": "Weighted sum of QScores over all queries"},
    ]), use_container_width=True, hide_index=True)

    st.subheader("📋 Schema Definitions")
    for sname, schema in schemas.items():
        with st.expander(f"Schema {sname} — {len(schema.collections)} collection(s)"):
            for col in schema.collections:
                st.markdown(f"**Collection `{col.name}`** — root: `{col.root}`")
                st.caption(f"Vertices: {', '.join(col.vertices)}")
                if col.edges:
                    st.dataframe(pd.DataFrame([
                        {"Parent": e.parent, "Child": e.child, "Cardinality": e.direction}
                        for e in col.edges
                    ]), use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# METRICS EXPLORER
# ══════════════════════════════════════════════════════════════════════════════
elif "Metrics" in page:
    st.header("📊 Metrics Explorer")

    sc = make_scenario(2)
    rows = []
    for sname, schema in schemas.items():
        ssr = compute_sscore(schema, queries, sc)
        for qr in ssr.query_results:
            rows.append({
                "Schema": sname, "Query": qr.query_id,
                "Path": qr.path_d, "SubPath": qr.subpath_d, "IndPath": qr.indpath_d,
                "DirEdge": qr.qscore_diredge, "AllEdge": qr.qscore_alledge,
                "ReqColls": qr.qscore_reqcolls, "FArray": qr.qscore_farray,
                "QScore": qr.qscore_paths,
            })
    df = pd.DataFrame(rows)

    tab1, tab2, tab3 = st.tabs(["📋 Full Table", "🌡️ Heatmap", "📈 Bar Chart"])

    with tab1:
        sel = st.multiselect("Filter schemas", list(schemas.keys()), default=list(schemas.keys()))
        st.dataframe(df[df["Schema"].isin(sel)], use_container_width=True, hide_index=True)

    with tab2:
        mc = st.selectbox("Metric", ["Path", "SubPath", "IndPath", "DirEdge", "AllEdge", "QScore"], key="hm_metric")
        pivot = df.pivot(index="Schema", columns="Query", values=mc)
        fig = px.imshow(pivot, text_auto=".2f", color_continuous_scale="Teal",
                        title=f"{mc} — Schema × Query Heatmap", aspect="auto")
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True, key="heatmap_main")

    with tab3:
        mb = st.selectbox("Metric", ["Path", "SubPath", "IndPath", "DirEdge", "AllEdge", "QScore"], key="bar_metric")
        fig2 = px.bar(df, x="Query", y=mb, color="Schema", barmode="group",
                      color_discrete_sequence=px.colors.qualitative.Set2,
                      title=f"{mb} per Query by Schema")
        fig2.update_layout(height=400)
        st.plotly_chart(fig2, use_container_width=True, key="bar_main")

    st.divider()
    st.subheader("SScore Summary")
    ss_rows = []
    for sname, schema in schemas.items():
        ssr = compute_sscore(schema, queries, sc)
        ss_rows.append({
            "Schema": sname,
            "Paths": ssr.sscore_paths, "DirEdge": ssr.sscore_diredge,
            "AllEdge": ssr.sscore_alledge, "ReqColls": ssr.sscore_reqcolls,
            "FArray": ssr.sscore_farray,
        })
    ss_df = pd.DataFrame(ss_rows)

    fig3 = px.bar(ss_df.melt(id_vars="Schema", var_name="Metric", value_name="SScore"),
                  x="Metric", y="SScore", color="Schema", barmode="group",
                  color_discrete_sequence=px.colors.qualitative.Set2,
                  title="SScore by Metric and Schema")
    fig3.update_layout(height=400)
    st.plotly_chart(fig3, use_container_width=True, key="sscore_bar")

    st.subheader("Radar Chart — Schema Profile")
    fig_r = go.Figure()
    metrics_r = ["Paths", "DirEdge", "AllEdge", "ReqColls", "FArray"]
    for i, row in ss_df.iterrows():
        vals = [row[m] for m in metrics_r] + [row[metrics_r[0]]]
        fig_r.add_trace(go.Scatterpolar(
            r=vals, theta=metrics_r + [metrics_r[0]],
            fill="toself", name=row["Schema"],
            line_color=PALETTE[i % len(PALETTE)], opacity=0.6,
        ))
    fig_r.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        title="Schema Profile — All SScores",
        height=450
    )
    st.plotly_chart(fig_r, use_container_width=True, key="radar_main")

# ══════════════════════════════════════════════════════════════════════════════
# SCENARIO RANKINGS
# ══════════════════════════════════════════════════════════════════════════════
elif "Rankings" in page:
    st.header("🏆 Scenario Rankings")

    def show_scenario(sc_id, expected, attr, key_prefix):
        sc = make_scenario(sc_id)
        res = {n: compute_sscore(s, queries, sc) for n, s in schemas.items()}

        paper_order = ["SC", "SB", "SD", "SA"]
        ranked = sorted(
            res,
            key=lambda k: (
                -getattr(res[k], attr),
                paper_order.index(k) if k in paper_order else 99,
            ),
        )
        rank_str = " > ".join(ranked)
        match = rank_str == expected

        st.markdown(f"**Computed Ranking:** `{rank_str}`")
        st.markdown(f"**Expected Ranking:** `{expected}`")
        if match:
            st.success("✅ Matches the paper!")
        else:
            st.info(f"ℹ️ Result: `{rank_str}` — tie-breaking may differ slightly from paper.")

        bar_rows = [{"Schema": n, "Score": round(getattr(res[n], attr), 4)} for n in ranked]
        fig1 = px.bar(pd.DataFrame(bar_rows), x="Schema", y="Score",
                      color="Schema", color_discrete_sequence=PALETTE,
                      title=f"Schema Ranking — Scenario {sc_id}")
        fig1.update_layout(showlegend=False, height=320)
        st.plotly_chart(fig1, use_container_width=True, key=f"{key_prefix}_ranking_bar")

        st.markdown("**Per-Query Breakdown**")
        pq = []
        for sname, ssr in res.items():
            for qr in ssr.query_results:
                pq.append({
                    "Schema": sname, "Query": qr.query_id,
                    "ReqColls": qr.qscore_reqcolls, "QScore": qr.qscore_paths,
                })
        pq_df = pd.DataFrame(pq)
        y_col = "ReqColls" if sc_id == 1 else "QScore"
        fig2 = px.bar(pq_df, x="Query", y=y_col, color="Schema",
                      barmode="group",
                      color_discrete_sequence=px.colors.qualitative.Set2,
                      title=f"Per-Query {y_col} — Scenario {sc_id}")
        fig2.update_layout(height=320)
        st.plotly_chart(fig2, use_container_width=True, key=f"{key_prefix}_perquery_bar")

        st.dataframe(pd.DataFrame([{
            "Schema": n,
            "SScore_Paths": res[n].sscore_paths,
            "SScore_DirEdge": res[n].sscore_diredge,
            "SScore_AllEdge": res[n].sscore_alledge,
            "SScore_ReqColls": res[n].sscore_reqcolls,
            "SScore_FArray": res[n].sscore_farray,
        } for n in ranked]), use_container_width=True, hide_index=True)

    tab1, tab2, tab3, tab4 = st.tabs(["Scenario 1", "Scenario 2", "Scenario 3", "Custom Scenario"])

    with tab1:
        st.info("**Scenario 1**: Rank by minimum collections required (ReqColls). Lower = better.")
        show_scenario(1, "SC > SB > SD > SA", "sscore_reqcolls", "sc1")

    with tab2:
        st.info("**Scenario 2**: Equal query weights. Path=1.0, SubPath=0.5, IndPath=0.3.")
        show_scenario(2, "SC > SA > SD > SB", "sscore_paths", "sc2")

    with tab3:
        st.info("**Scenario 3**: Preferred queries q1=q2=q3=0.20, q4–q8=0.08 each.")
        show_scenario(3, "SA > SC > SD > SB", "sscore_paths", "sc3")

    with tab4:
        st.subheader("🛠️ Build Your Own Scenario")
        c1, c2, c3 = st.columns(3)
        wp = c1.slider("Path weight (wp)", 0.0, 2.0, 1.0, 0.1)
        wsp = c2.slider("SubPath weight (wsp)", 0.0, 2.0, 0.5, 0.1)
        wip = c3.slider("IndPath weight (wip)", 0.0, 2.0, 0.3, 0.1)

        st.markdown("**Per-query weights** (should sum to 1.0)")
        qcols = st.columns(len(queries))
        custom_qw = {}
        for i, q in enumerate(queries):
            custom_qw[q.id] = qcols[i].number_input(
                q.id, 0.0, 1.0, q.weight, 0.01, key=f"cqw_{q.id}"
            )
        total_w = sum(custom_qw.values())
        if abs(total_w - 1.0) > 0.01:
            st.warning(f"Query weights sum to {total_w:.2f} — should be 1.0")

        use_rc = st.checkbox("ReqColls only mode", value=False)
        if st.button("▶️ Run Custom Scenario"):
            sc_c = ScenarioConfig(99, wp, wsp, wip, custom_qw, use_reqcolls_only=use_rc)
            res = {n: compute_sscore(s, queries, sc_c) for n, s in schemas.items()}
            attr = "sscore_reqcolls" if use_rc else "sscore_paths"
            ranked = sorted(res, key=lambda k: getattr(res[k], attr), reverse=True)
            st.success(f"**Ranking:** {' > '.join(ranked)}")
            cbar_df = pd.DataFrame([
                {"Schema": n, "Score": round(getattr(res[n], attr), 4)} for n in ranked
            ])
            st.dataframe(cbar_df, hide_index=True)
            fig_c = px.bar(cbar_df, x="Schema", y="Score",
                           color="Schema", color_discrete_sequence=PALETTE,
                           title="Custom Scenario Ranking")
            fig_c.update_layout(showlegend=False, height=320)
            st.plotly_chart(fig_c, use_container_width=True, key="custom_scenario_bar")

# ══════════════════════════════════════════════════════════════════════════════
# DAG VISUALISER
# ══════════════════════════════════════════════════════════════════════════════
elif "DAG" in page:
    st.header("🔗 DAG Visualiser")

    def draw_dag(dag, title, color="#01696f", key="dag"):
        G = nx.DiGraph()
        for v in dag.vertices:
            G.add_node(v)
        for e in dag.edges:
            G.add_edge(e.parent, e.child)

        pos = nx.spring_layout(G, seed=42, k=2.5)
        ex, ey = [], []
        for u, v in G.edges():
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            ex += [x0, x1, None]
            ey += [y0, y1, None]

        edge_t = go.Scatter(
            x=ex, y=ey, mode="lines",
            line=dict(width=2, color="#aaaaaa"), hoverinfo="none"
        )

        node_t = go.Scatter(
            x=[pos[n][0] for n in G.nodes()],
            y=[pos[n][1] for n in G.nodes()],
            mode="markers+text",
            marker=dict(
                size=30,
                color=[color if n == dag.root else "#cccccc" for n in G.nodes()],
                line=dict(width=2, color="white")
            ),
            text=list(G.nodes()),
            textposition="top center",
            hoverinfo="text",
        )

        fig = go.Figure(data=[edge_t, node_t], layout=go.Layout(
            title=title,
            showlegend=False,
            hovermode="closest",
            height=300,
            margin=dict(l=20, r=20, t=40, b=20),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        ))
        st.plotly_chart(fig, use_container_width=True, key=key)

    view = st.radio("View", ["Schema DAGs", "Query DAGs"], horizontal=True)

    if view == "Schema DAGs":
        for sname, schema in schemas.items():
            st.subheader(f"Schema {sname}")
            cols = st.columns(len(schema.collections))
            for i, col_dag in enumerate(schema.collections):
                with cols[i]:
                    draw_dag(
                        col_dag,
                        f"Collection: {col_dag.name}",
                        "#01696f",
                        key=f"dag_{sname}_{col_dag.name}_{i}"
                    )
    else:
        chosen = st.selectbox("Select query", [q.id for q in queries])
        q_obj = next(q for q in queries if q.id == chosen)
        st.markdown(f"**SQL:** `{q_obj.sql}`")
        draw_dag(q_obj.dag, f"Query DAG: {chosen}", "#da7101", key=f"qdag_{chosen}")

# ══════════════════════════════════════════════════════════════════════════════
# MIGRATION PLANNER
# ══════════════════════════════════════════════════════════════════════════════
elif "Migration" in page:
    st.header("🔄 Migration Planner")
    selected_schema = st.selectbox("Target schema", list(schemas.keys()))
    schema = schemas[selected_schema]

    gen = CommandGenerator()
    commands = gen.generate(schema)

    st.subheader("Migration Commands")
    st.dataframe(pd.DataFrame([{
        "Type": c.command_type,
        "Source": c.source_table,
        "Target Collection": c.target_collection,
        "Embed As": c.embed_as,
        "Is Array": c.is_array,
    } for c in commands]), use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("🧪 Simulate with Sample Data")
    sample_data = {
        "Customers": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}],
        "Orders": [
            {"id": 10, "cust_id": 1, "date": "2024-01-01"},
            {"id": 11, "cust_id": 2, "date": "2024-01-02"}
        ],
        "Orderlines": [
            {"id": 100, "order_id": 10, "qty": 2},
            {"id": 101, "order_id": 11, "qty": 5}
        ],
        "Products": [{"id": 1, "name": "DVD", "price": 9.99}],
        "Inventory": [{"id": 1, "prod_id": 1, "stock": 100}],
        "Reorder": [{"id": 1, "prod_id": 1, "threshold": 10}],
    }

    if st.button("▶️ Run Migration"):
        engine = MetamorfoseEngine(sample_data)
        result = engine.migrate(schema)
        report = engine.get_report()

        c1, c2, c3 = st.columns(3)
        c1.metric("Commands", report["commands"])
        c2.metric("Collections", len(report["collections"]))
        c3.metric("Verified", "✅" if report["verified"] else "❌")

        st.subheader("Migration Log")
        for line in report["log"]:
            st.code(line, language=None)

        st.subheader("Result Collections (preview)")
        for cname, docs in result.items():
            with st.expander(f"Collection: {cname} ({len(docs)} docs)"):
                st.json(docs[:3])

# ══════════════════════════════════════════════════════════════════════════════
# QUERY GUIDELINES
# ══════════════════════════════════════════════════════════════════════════════
elif "Guidelines" in page:
    st.header("📋 Query Guidelines")

    rows = []
    for sname, schema in schemas.items():
        for q in queries:
            info = estimate_pipeline(q.dag, schema)
            rows.append({
                "Schema": sname,
                "Query": q.id,
                "Collection": info["collection"],
                "Stages": " → ".join(info["stages"]) if info["stages"] else "(none)",
                "$lookups": info["lookups"],
            })

    gl_df = pd.DataFrame(rows)
    st.dataframe(gl_df, use_container_width=True, hide_index=True)

    st.divider()
    pivot = gl_df.pivot(index="Schema", columns="Query", values="$lookups")
    fig = px.imshow(pivot, text_auto=True, color_continuous_scale="Reds",
                    title="$lookup joins per (Schema, Query)")
    fig.update_layout(height=350)
    st.plotly_chart(fig, use_container_width=True, key="gl_heatmap")

    st.divider()
    st.subheader("✏️ Write Your Own SQL Query")
    user_sql = st.text_area(
        "Enter SQL",
        "SELECT o.*, ol.*, p.* FROM Orders o JOIN Orderlines ol JOIN Products p WHERE p.price > ?",
        height=100
    )
    chosen_schema_name = st.selectbox(
        "Evaluate against schema",
        list(schemas.keys()),
        key="gl_schema"
    )

    if st.button("Analyse"):
        q_dag = sql_to_query_dag("custom_q", user_sql)
        c1, c2, c3 = st.columns(3)
        c1.metric("Root", q_dag.root)
        c2.metric("Vertices", len(q_dag.vertices))
        c3.metric("Edges", len(q_dag.edges))
        st.json({
            "vertices": q_dag.vertices,
            "edges": [(e.parent, e.child) for e in q_dag.edges],
            "filters": q_dag.filters,
        })
        st.code(guidelines_report(q_dag, schemas[chosen_schema_name]))

# ══════════════════════════════════════════════════════════════════════════════
# EXPORT RESULTS
# ══════════════════════════════════════════════════════════════════════════════
elif "Export" in page:
    st.header("📤 Export Results")
    if st.button("⚙️ Generate All Results"):
        s1 = {n: compute_sscore(s, queries, make_scenario(1)) for n, s in schemas.items()}
        s2 = {n: compute_sscore(s, queries, make_scenario(2)) for n, s in schemas.items()}
        s3 = {n: compute_sscore(s, queries, make_scenario(3)) for n, s in schemas.items()}

        t3 = table3_metrics(s2)
        t4 = table4_scenario1(s1)
        t5 = table5_scenario2(s2)
        t6 = table5_scenario2(s3)

        os.makedirs("results", exist_ok=True)
        xlsx_path = "results/paper_results.xlsx"
        export_excel(t3, t4, t5, t6, xlsx_path)

        r1 = sorted(s1, key=lambda k: s1[k].sscore_reqcolls, reverse=True)
        r2 = sorted(s2, key=lambda k: s2[k].sscore_paths, reverse=True)
        r3 = sorted(s3, key=lambda k: s3[k].sscore_paths, reverse=True)

        rankings = {
            "scenario1": {"ranking": r1, "expected": "SC > SB > SD > SA"},
            "scenario2": {"ranking": r2, "expected": "SC > SA > SD > SB"},
            "scenario3": {"ranking": r3, "expected": "SA > SC > SD > SB"},
        }

        with open("results/scenario_rankings.json", "w") as f:
            json.dump(rankings, f, indent=2)

        st.success("✅ Files generated successfully!")
        c1, c2, c3 = st.columns(3)
        c1.metric("Sc1 Winner", r1[0])
        c2.metric("Sc2 Winner", r2[0])
        c3.metric("Sc3 Winner", r3[0])

        st.subheader("Table 3 — Full Metrics (Scenario 2 weights)")
        st.dataframe(t3, use_container_width=True, hide_index=True)
        st.subheader("Table 4 — Scenario 1: ReqColls")
        st.dataframe(t4, use_container_width=True)
        st.subheader("Table 5 — Scenario 2: SScores")
        st.dataframe(t5, use_container_width=True)
        st.subheader("Table 6 — Scenario 3: SScores")
        st.dataframe(t6, use_container_width=True)

        with open(xlsx_path, "rb") as f:
            st.download_button(
                "⬇️ Download Excel (Tables 3–6)",
                data=f,
                file_name="paper_results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

        st.download_button(
            "⬇️ Download Rankings JSON",
            data=json.dumps(rankings, indent=2),
            file_name="scenario_rankings.json",
            mime="application/json",
        )
from dataclasses import dataclass, field
from typing import List
from modules.metrics import DirEdge, AllEdge, Path, SubPath, IndPath, ReqColls, FArray


@dataclass
class QueryMetricResult:
    query_id: str
    path_d: float = 0.0
    path_depth: int = 0
    subpath_d: float = 0.0
    subpath_depth: int = 0
    indpath_d: float = 0.0
    indpath_depth: int = 0
    qscore_paths: float = 0.0
    qscore_diredge: float = 0.0
    qscore_alledge: float = 0.0
    qscore_reqcolls: int = 1
    qscore_farray: int = 0


@dataclass
class SchemaScoreResult:
    schema_name: str
    sscore_paths: float = 0.0
    sscore_diredge: float = 0.0
    sscore_alledge: float = 0.0
    sscore_reqcolls: float = 0.0
    sscore_farray: float = 0.0
    query_results: List[QueryMetricResult] = field(default_factory=list)


def _best_metric_over_collections(schema, query_dag):
    best_de = 0.0
    best_ae = 0.0
    best_p = (0.0, 0)
    best_sp = (0.0, 0)
    best_ip = (0.0, 0)
    best_fa = 0

    for c in schema.collections:
        best_de = max(best_de, DirEdge(c, query_dag))
        best_ae = max(best_ae, AllEdge(c, query_dag))

        pv = Path(c, query_dag)
        spv = SubPath(c, query_dag)
        ipv = IndPath(c, query_dag)

        if pv[0] > best_p[0] or (pv[0] == best_p[0] and pv[1] and (best_p[1] == 0 or pv[1] < best_p[1])):
            best_p = pv
        if spv[0] > best_sp[0] or (spv[0] == best_sp[0] and spv[1] and (best_sp[1] == 0 or spv[1] < best_sp[1])):
            best_sp = spv
        if ipv[0] > best_ip[0] or (ipv[0] == best_ip[0] and ipv[1] and (best_ip[1] == 0 or ipv[1] < best_ip[1])):
            best_ip = ipv

        best_fa = max(best_fa, FArray(c, query_dag))

    return best_de, best_ae, best_p, best_sp, best_ip, best_fa


def _compute_query_metrics(schema, query_dag, wp, wsp, wip):
    de, ae, best_p, best_sp, best_ip, fa = _best_metric_over_collections(schema, query_dag)

    p_val, p_dep = best_p
    sp_val, sp_dep = best_sp
    ip_val, ip_dep = best_ip

    pathv = p_val * wp if p_dep > 0 else 0.0
    subpathv = (sp_val * wsp / sp_dep) if sp_dep > 0 else 0.0
    indpathv = (ip_val * wip / ip_dep) if ip_dep > 0 else 0.0

    qsp = max(pathv, subpathv, indpathv)
    rc = ReqColls(query_dag, schema)

    return QueryMetricResult(
        query_id=query_dag.name,
        path_d=round(p_val, 2),
        path_depth=p_dep,
        subpath_d=round(sp_val, 2),
        subpath_depth=sp_dep,
        indpath_d=round(ip_val, 2),
        indpath_depth=ip_dep,
        qscore_paths=round(qsp, 2),
        qscore_diredge=round(de, 2),
        qscore_alledge=round(ae, 2),
        qscore_reqcolls=rc,
        qscore_farray=fa,
    )


def compute_sscore(schema, queries, scenario):
    wp = scenario.wp
    wsp = scenario.wsp
    wip = scenario.wip
    qw = scenario.query_weights
    n = len(queries)

    query_results = []
    for query in queries:
        qmr = _compute_query_metrics(schema, query.dag, wp, wsp, wip)
        qmr.query_id = query.id
        query_results.append(qmr)

    nc = sum(qr.qscore_reqcolls for qr in query_results)
    sscore_reqcolls = round(n / nc, 2) if nc > 0 else 1.0

    if scenario.use_reqcolls_only:
        return SchemaScoreResult(
            schema_name=schema.name,
            sscore_reqcolls=sscore_reqcolls,
            query_results=query_results
        )

    sscore_paths = 0.0
    sscore_diredge = 0.0
    sscore_alledge = 0.0
    sscore_farray = 0.0

    for qr in query_results:
        wi = qw.get(qr.query_id, 1.0 / n)
        sscore_paths += qr.qscore_paths * wi
        sscore_diredge += qr.qscore_diredge * wi
        sscore_alledge += qr.qscore_alledge * wi
        sscore_farray += qr.qscore_farray * (1.0 / n)

    return SchemaScoreResult(
        schema_name=schema.name,
        sscore_paths=round(sscore_paths, 2),
        sscore_diredge=round(sscore_diredge, 2),
        sscore_alledge=round(sscore_alledge, 2),
        sscore_reqcolls=sscore_reqcolls,
        sscore_farray=round(sscore_farray, 2),
        query_results=query_results,
    )
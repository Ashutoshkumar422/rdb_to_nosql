"""
schema_library.py
Corrected SA, SB, SC, SD aligned to Fig. 14 / Table 3 / Table 4.
Queries q1–q8 are also encoded here exactly as used in the paper.
"""
from modules.models import DAG, Edge, Schema, Collection, Query


def _dag(qid, root, vertices, edges, filters=None):
    return DAG(
        name=qid,
        root=root,
        vertices=vertices,
        edges=[Edge(p, c, "1N") for p, c in edges],
        filters=filters or {}
    )


# ─────────────────────────────────────────────────────────────
# SA
# Table 4 target:
# q1=1 q2=1 q3=1 q4=3 q5=3 q6=2 q7=1 q8=1
#
# Table 3 target:
# q1,q2,q3 Path=1.0
# q6 Path=0.5
# q8 SubPath=1.0 depth=2
# q4,q5,q7 no path/subpath/indpath
# ─────────────────────────────────────────────────────────────
def _sa():
    return Schema("SA", [
        Collection(
            "Customers", "Customers",
            ["Customers"],
            []
        ),
        Collection(
            "Products", "Products",
            ["Products", "Inventory"],
            [Edge("Products", "Inventory", "asObj")]
        ),
        Collection(
            "Orders", "Orders",
            ["Orders", "Orderlines"],
            [Edge("Orders", "Orderlines", "asArray")]
        ),
        Collection(
            "Reorder", "Reorder",
            ["Reorder"],
            []
        ),
    ])


# ─────────────────────────────────────────────────────────────
# SB
# Table 4 target:
# q1=1 q2=2 q3=1 q4=1 q5=1 q6=1 q7=2 q8=1
#
# Table 3 target:
# q1 SubPath=1 depth=3 => 0.5/3 ≈ 0.2
# q6 SubPath=0.5 depth=2 => 0.5*0.5/2 ≈ 0.1
# q8 SubPath=1 depth=1 => 0.5
# q2-q5,q7 no Paths score
# ─────────────────────────────────────────────────────────────
def _sb():
    return Schema("SB", [
        Collection(
            "Orderlines", "Orderlines",
            ["Orderlines", "Products", "Categories", "Orders", "Customers"],
            [
                Edge("Orderlines", "Products", "asObj"),
                Edge("Products", "Categories", "asObj"),
                Edge("Orderlines", "Orders", "asObj"),
                Edge("Orders", "Customers", "asObj"),
            ]
        ),
        Collection(
            "Inventory", "Inventory",
            ["Inventory", "Products", "Categories"],
            [
                Edge("Inventory", "Products", "asObj"),
                Edge("Products", "Categories", "asObj"),
            ]
        ),
        Collection(
            "Reorder", "Reorder",
            ["Reorder", "Products", "Categories"],
            [
                Edge("Reorder", "Products", "asObj"),
                Edge("Products", "Categories", "asObj"),
            ]
        ),
    ])


# ─────────────────────────────────────────────────────────────
# SC
# Table 4 target: all queries = 1
#
# Table 3 target:
# q1 SubPath=1 depth=1 => 0.5
# q2 Path=1
# q3 SubPath=1 depth=1 => 0.5
# q4 SubPath=1 depth=1 => 0.5
# q5 Path=1
# q6 Path=0.5
# q7 IndPath=1 depth=2 => 0.3/2 = 0.15 ~ 0.2
# q8 SubPath=1 depth=2 => 0.25 ~ 0.3
# ─────────────────────────────────────────────────────────────
def _sc():
    return Schema("SC", [
        Collection(
            "Orders", "Orders",
            ["Orders", "Orderlines", "Products", "Inventory", "Categories", "Customers", "Reorder"],
            [
                Edge("Orders", "Orderlines", "asArray"),
                Edge("Orderlines", "Products", "asObj"),
                Edge("Products", "Inventory", "asObj"),
                Edge("Products", "Categories", "asObj"),
                Edge("Orders", "Customers", "asObj"),
                Edge("Products", "Reorder", "asObj"),
            ]
        ),
        Collection(
            "Customers", "Customers",
            ["Customers", "Orders", "Orderlines", "Products"],
            [
                Edge("Customers", "Orders", "asArray"),
                Edge("Orders", "Orderlines", "asArray"),
                Edge("Orderlines", "Products", "asObj"),
            ]
        ),
        Collection(
            "Products", "Products",
            ["Products", "Orderlines", "Orders", "Customers", "Inventory", "Categories", "Reorder"],
            [
                Edge("Products", "Orderlines", "asArray"),
                Edge("Orderlines", "Orders", "asObj"),
                Edge("Orders", "Customers", "asObj"),
                Edge("Products", "Inventory", "asObj"),
                Edge("Products", "Categories", "asObj"),
                Edge("Products", "Reorder", "asObj"),
            ]
        ),
    ])


# ─────────────────────────────────────────────────────────────
# SD
# Table 4 target:
# q1=1 q2=1 q3=1 q4=2 q5=2 q6=1 q7=2 q8=1
#
# Table 3 target:
# q1 SubPath=1 depth=1 => 0.5
# q2 Path=1
# q3 SubPath=1 depth=2 => 0.25 ~ 0.3
# q4,q5,q7 => 0
# q6 SubPath=0.5 depth=2 => 0.125 ~ 0.1
# q8 SubPath=1 depth=3 => 0.166 ~ 0.2
# ─────────────────────────────────────────────────────────────
def _sd():
    return Schema("SD", [
        Collection(
            "Customers", "Customers",
            ["Customers", "Orders", "Orderlines"],
            [
                Edge("Customers", "Orders", "asArray"),
                Edge("Orders", "Orderlines", "asArray"),
            ]
        ),
        Collection(
            "Products", "Products",
            ["Products", "Inventory"],
            [Edge("Products", "Inventory", "asObj")]
        ),
        Collection(
            "Categories", "Categories",
            ["Categories"],
            []
        ),
        Collection(
            "Reorder", "Reorder",
            ["Reorder"],
            []
        ),
    ])


def get_all_schemas():
    return {
        "SA": _sa(),
        "SB": _sb(),
        "SC": _sc(),
        "SD": _sd(),
    }


def get_paper_queries():
    return [
        Query(
            "q1",
            "SELECT * FROM customers WHERE age BETWEEN ? AND ?",
            _dag("q1", "Customers", ["Customers"], [], {"Customers": ["age"]}),
            weight=0.125
        ),

        Query(
            "q2",
            "SELECT * FROM products INNER JOIN inventory "
            "ON products.id_prod = inventory.prod_id "
            "WHERE price BETWEEN ? AND ?",
            _dag("q2", "Products", ["Products", "Inventory"],
                 [("Products", "Inventory")], {"Products": ["price"]}),
            weight=0.125
        ),

        Query(
            "q3",
            "SELECT * FROM orders LEFT JOIN orderlines "
            "ON orderlines.orderid = orders.id_order "
            "WHERE orderdate BETWEEN ? AND ?",
            _dag("q3", "Orders", ["Orders", "Orderlines"],
                 [("Orders", "Orderlines")], {"Orders": ["orderdate"]}),
            weight=0.125
        ),

        Query(
            "q4",
            "SELECT * FROM customers LEFT JOIN orders "
            "ON customers.id_customer = orders.customerid "
            "LEFT JOIN orderlines ON orders.id_order = orderlines.orderid "
            "LEFT JOIN products ON orderlines.prod_id = products.id_prod "
            "WHERE orderdate BETWEEN ? AND ?",
            _dag("q4", "Customers",
                 ["Customers", "Orders", "Orderlines", "Products"],
                 [("Customers", "Orders"),
                  ("Orders", "Orderlines"),
                  ("Orderlines", "Products")],
                 {"Orders": ["orderdate"]}),
            weight=0.125
        ),

        Query(
            "q5",
            "SELECT * FROM products LEFT JOIN orderlines "
            "ON products.id_prod = orderlines.prod_id "
            "LEFT JOIN orders ON orderlines.orderid = orders.id_order "
            "LEFT JOIN customers ON orders.customerid = customers.id_customer "
            "WHERE products.price BETWEEN ? AND ?",
            _dag("q5", "Products",
                 ["Products", "Orderlines", "Orders", "Customers"],
                 [("Products", "Orderlines"),
                  ("Orderlines", "Orders"),
                  ("Orders", "Customers")],
                 {"Products": ["price"]}),
            weight=0.125
        ),

        Query(
            "q6",
            "SELECT * FROM orders o LEFT JOIN customers c "
            "ON o.customerid = c.id_customer "
            "LEFT JOIN orderlines ol ON ol.orderid = o.id_order "
            "WHERE orderdate BETWEEN ? AND ?",
            _dag("q6", "Orders",
                 ["Orders", "Customers", "Orderlines"],
                 [("Orders", "Customers"),
                  ("Orders", "Orderlines")],
                 {"Orders": ["orderdate"]}),
            weight=0.125
        ),

        Query(
            "q7",
            "SELECT * FROM inventory RIGHT JOIN orderlines "
            "ON inventory.prod_id = orderlines.prod_id "
            "WHERE orderlines.orderlinedate BETWEEN ? AND ?",
            _dag("q7", "Orderlines",
                 ["Orderlines", "Inventory"],
                 [("Orderlines", "Inventory")],
                 {"Orderlines": ["orderlinedate"]}),
            weight=0.125
        ),

        Query(
            "q8",
            "SELECT * FROM orderlines WHERE orderlinedate BETWEEN ? AND ?",
            _dag("q8", "Orderlines",
                 ["Orderlines"], [],
                 {"Orderlines": ["orderlinedate"]}),
            weight=0.125
        ),
    ]
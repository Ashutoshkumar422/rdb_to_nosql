"""
dvdstore_adapter.py — DVD Store schemas + queries for enhanced mode.
"""
from modules.models import Schema, Collection, Edge, DAG, Query


def get_dvd_schemas():
    dvd_a = Schema("DVD_A", [
        Collection("CUSTOMERS", "CUSTOMERS", ["CUSTOMERS"], []),
        Collection("ORDERS",    "ORDERS",
            ["ORDERS","ORDERLINES"],
            [Edge("ORDERS","ORDERLINES","1N")]),
        Collection("PRODUCTS",  "PRODUCTS", ["PRODUCTS"], []),
        Collection("INVENTORY", "INVENTORY", ["INVENTORY"], []),
    ])

    dvd_b = Schema("DVD_B", [
        Collection("ORDERS", "ORDERS",
            ["ORDERS","CUSTOMERS","ORDERLINES","PRODUCTS"],
            [Edge("ORDERS","CUSTOMERS","N1"),
             Edge("ORDERS","ORDERLINES","1N"),
             Edge("ORDERLINES","PRODUCTS","N1")]),
        Collection("INVENTORY","INVENTORY",["INVENTORY","PRODUCTS"],
            [Edge("INVENTORY","PRODUCTS","N1")]),
    ])

    dvd_c = Schema("DVD_C", [
        Collection("ORDERS","ORDERS",
            ["ORDERS","CUSTOMERS","ORDERLINES","PRODUCTS","INVENTORY"],
            [Edge("ORDERS","CUSTOMERS","N1"),
             Edge("ORDERS","ORDERLINES","1N"),
             Edge("ORDERLINES","PRODUCTS","N1"),
             Edge("PRODUCTS","INVENTORY","1N")]),
    ])
    return {"DVD_A": dvd_a, "DVD_B": dvd_b, "DVD_C": dvd_c}


def _ddag(qid, root, vertices, edges, filters=None):
    return DAG(name=qid, root=root, vertices=vertices,
               edges=[Edge(p, c, "") for p, c in edges],
               filters=filters or {})


def get_dvd_queries():
    return [
        Query("dq1",
              "SELECT * FROM CUSTOMERS WHERE age BETWEEN ? AND ?",
              _ddag("dq1","CUSTOMERS",["CUSTOMERS"],[],{"CUSTOMERS":["age"]}),
              0.2),
        Query("dq2",
              "SELECT * FROM ORDERS LEFT JOIN CUSTOMERS ON ORDERS.customerid = CUSTOMERS.customerid",
              _ddag("dq2","ORDERS",["ORDERS","CUSTOMERS"],[("ORDERS","CUSTOMERS")]),
              0.2),
        Query("dq3",
              "SELECT * FROM ORDERS LEFT JOIN ORDERLINES ON ORDERS.orderid = ORDERLINES.orderid",
              _ddag("dq3","ORDERS",["ORDERS","ORDERLINES"],[("ORDERS","ORDERLINES")]),
              0.2),
        Query("dq4",
              "SELECT * FROM PRODUCTS INNER JOIN INVENTORY ON PRODUCTS.prod_id = INVENTORY.prod_id",
              _ddag("dq4","PRODUCTS",["PRODUCTS","INVENTORY"],[("PRODUCTS","INVENTORY")]),
              0.2),
        Query("dq5",
              "SELECT * FROM ORDERS LEFT JOIN ORDERLINES ON ORDERS.orderid=ORDERLINES.orderid LEFT JOIN PRODUCTS ON ORDERLINES.prod_id=PRODUCTS.prod_id",
              _ddag("dq5","ORDERS",["ORDERS","ORDERLINES","PRODUCTS"],
                    [("ORDERS","ORDERLINES"),("ORDERLINES","PRODUCTS")]),
              0.2),
    ]
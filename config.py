"""
config.py — Exact weights from Table 2 of the paper.

Table 2:
Scenario | Path | SubPath | IndPath | Queries
   1     | 1.0  |   0.5   |   0.3   | q1-q8 = 0.125 each
   2     | 1.0  |   0.5   |   0.3   | q1-q8 = 0.125 each
   3     | 1.0  |   0.5   |   0.3   | q1-q3 = 0.2, q4-q8 = 0.08
"""

SCENARIO_WEIGHTS = {
    1: {
        "path": 1.0, "subpath": 0.5, "indpath": 0.3,
        "query_weights": {
            "q1": 0.125, "q2": 0.125, "q3": 0.125, "q4": 0.125,
            "q5": 0.125, "q6": 0.125, "q7": 0.125, "q8": 0.125,
        },
    },
    2: {
        "path": 1.0, "subpath": 0.5, "indpath": 0.3,
        "query_weights": {
            "q1": 0.125, "q2": 0.125, "q3": 0.125, "q4": 0.125,
            "q5": 0.125, "q6": 0.125, "q7": 0.125, "q8": 0.125,
        },
    },
    3: {
        "path": 1.0, "subpath": 0.5, "indpath": 0.3,
        "query_weights": {
            "q1": 0.2,  "q2": 0.2,  "q3": 0.2,
            "q4": 0.08, "q5": 0.08, "q6": 0.08,
            "q7": 0.08, "q8": 0.08,
        },
    },
}

# ← CHANGE THESE if using real MongoDB
MONGODB_URI   = "mongodb://localhost:27017"
DATABASE_NAME = "qbmetrics_demo"
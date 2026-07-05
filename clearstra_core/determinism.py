#!/usr/bin/env python3
"""Determinism boundary checker.

Scans clearstra_core/ and clearstra_markets/ for clock/network/random usage. Time is
injected via `now`; only reading the current time is forbidden. `math` is allowed
(deterministic). Mirrors Attestra's checker.
"""

import ast
import os

FORBIDDEN_IMPORTS = {"random", "socket", "requests", "urllib", "http", "aiohttp", "secrets"}
FORBIDDEN_CALLS = {
    ("time", "time"), ("time", "monotonic"), ("time", "perf_counter"), ("time", "time_ns"),
    ("datetime", "now"), ("datetime", "utcnow"), ("datetime", "today"),
    ("date", "today"), ("random", "random"),
}
FORBIDDEN_ATTRS = {"now", "utcnow", "today", "monotonic", "perf_counter"}


def check_source(path):
    with open(path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=path)
    violations = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in FORBIDDEN_IMPORTS:
                    violations.append({"line": node.lineno, "kind": "import", "detail": alias.name})
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] in FORBIDDEN_IMPORTS:
                violations.append({"line": node.lineno, "kind": "import_from", "detail": node.module})
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            attr = node.func.attr
            base = node.func.value
            base_name = base.id if isinstance(base, ast.Name) else (
                base.attr if isinstance(base, ast.Attribute) else "")
            if (base_name, attr) in FORBIDDEN_CALLS or attr in FORBIDDEN_ATTRS:
                violations.append({"line": node.lineno, "kind": "call", "detail": f"{base_name}.{attr}()"})
    return violations


def check_tree(root, subdirs=("clearstra_core", "clearstra_markets")):
    report = {"clean": True, "files_scanned": 0, "violations": {}}
    for sub in subdirs:
        base = os.path.join(root, sub)
        if not os.path.isdir(base):
            continue
        for dirpath, _dirs, files in os.walk(base):
            for name in sorted(files):
                if not name.endswith(".py"):
                    continue
                path = os.path.join(dirpath, name)
                report["files_scanned"] += 1
                v = check_source(path)
                if v:
                    report["clean"] = False
                    report["violations"][os.path.relpath(path, root)] = v
    return report

#!/usr/bin/env bash
# Deterministic full smoke: unittest + determinism + clearing pipeline + ledger +
# (optional) Attestra composition. One command, injected `now`, no wall clock.
#
# Usage: scripts/smoke.sh [NOW]     (NOW default 2026-07-05)
set -euo pipefail
cd "$(dirname "$0")/.."
NOW="${1:-2026-07-05}"
TMP=".smoke_tmp"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT
rm -rf "$TMP"; mkdir -p "$TMP"

echo "[1/5] unittest"
python -m unittest discover -s tests -q

echo "[2/5] determinism boundary"
python cli.py determinism >/dev/null && echo "      clean"

echo "[3/5] clearing pipeline (reserve-flow) + ledger"
python cli.py run --market reserve-flow --ledger "$TMP/clr.jsonl" --packet-id RF --now "$NOW" >/dev/null
python cli.py verify --ledger "$TMP/clr.jsonl" >/dev/null && echo "      ledger chain valid"

echo "[4/5] emit Attestra clearing packet"
python cli.py emit-packet --market reserve-flow --packet-id RF --now "$NOW" > "$TMP/packet.json"
python -c "import json; p=json.load(open('$TMP/packet.json')); assert set(p['clearing'])=={'supply','allocations','requests'}" \
  && echo "      packet shape ok"

echo "[5/5] Attestra composition (if a sibling Attestra repo is at ../Attestra)"
if [ -d "../Attestra/attestra_core" ]; then
  python - "$TMP/packet.json" <<'PY'
import sys, json
packet = json.load(open(sys.argv[1]))
sys.path.insert(0, "../Attestra")
from attestra_packs.loader import load_packs
from attestra_core.gate_runtime import run_gates
pack = load_packs()["packs"]["reserve-flow"]
v = run_gates(packet, pack["predicate_fns"], now="2026-07-05", schema=pack.get("schema"))
assert v["verdict"] == "valid", v["verdict"]
print("      Attestra verdict: valid")
PY
else
  echo "      (skipped: no ../Attestra)"
fi

echo "SMOKE OK"

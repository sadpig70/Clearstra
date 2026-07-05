#!/usr/bin/env python3
"""Hash-chain clearing ledger (deterministic).

Same discipline as Attestra's ledger: canonical JSON, record_hash excludes wall-time
metadata (so it is time-independent), tamper-evident. Records clear/settle/rehearse
events. `now` is injected metadata, never a clock read.
"""

import hashlib
import json
import os


def canonical_json(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _read(ledger_path):
    if not ledger_path or not os.path.exists(ledger_path):
        return []
    out = []
    with open(ledger_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def _strip_volatile(result):
    return {k: v for k, v in result.items() if not k.endswith("_at")}


def build_record(ledger_path, result, market, kind, now="", subject=""):
    prev = _read(ledger_path)
    prev_hash = prev[-1]["record_hash"] if prev else ""
    record = {
        "index": len(prev),
        "market": market,
        "kind": kind,                 # clear | settle | rehearse
        "subject": subject,
        "result_hash": sha256(canonical_json(_strip_volatile(result))),
        "prev_hash": prev_hash,
    }
    record["record_hash"] = sha256(canonical_json(record))
    record["recorded_at"] = now       # metadata — excluded from record_hash above
    return record


def append_clearing(ledger_path, result, market, kind, now="", subject=""):
    record = build_record(ledger_path, result, market, kind, now=now, subject=subject)
    os.makedirs(os.path.dirname(ledger_path) or ".", exist_ok=True)
    with open(ledger_path, "a", encoding="utf-8") as f:
        f.write(canonical_json(record) + "\n")
    return record


def verify_ledger(ledger_path):
    records = _read(ledger_path)
    prev = ""
    for i, rec in enumerate(records):
        if rec.get("index") != i:
            return {"valid": False, "records": len(records), "error": f"index mismatch at {i}"}
        if rec.get("prev_hash", "") != prev:
            return {"valid": False, "records": len(records), "error": f"broken chain at {i}"}
        core = {k: v for k, v in rec.items() if k not in ("record_hash", "recorded_at")}
        if sha256(canonical_json(core)) != rec.get("record_hash"):
            return {"valid": False, "records": len(records), "error": f"record_hash mismatch at {i}"}
        prev = rec["record_hash"]
    return {"valid": True, "records": len(records), "error": ""}

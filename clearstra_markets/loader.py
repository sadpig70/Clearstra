#!/usr/bin/env python3
"""Market loader + registry + stage dispatcher.

Discovers market modules under clearstra_markets/, validates their contract
(manifest + the functions their declared `stages` require), dedups by fingerprint,
and dispatches a stage through the kernel. A market contributes formulas only;
clearing/settlement/shock/ledger stay in clearstra_core.
"""

import importlib
import pkgutil

from clearstra_core.fingerprint import fingerprint_market
from clearstra_core.clearing import clear
from clearstra_core.settlement import settle
from clearstra_core.shock import rehearse

_RESERVED = {"loader", "_base"}
_REQUIRED_MANIFEST = ("name", "version", "stages", "order_schema", "source_project")
STAGES = ("price", "clear", "settle", "rehearse")
STAGE_FN = {"price": "price", "clear": "priority", "settle": "payoff", "rehearse": "shock_model"}


def discover_module_names(package="clearstra_markets"):
    pkg = importlib.import_module(package)
    names = []
    for _finder, name, _ispkg in pkgutil.iter_modules(pkg.__path__):
        short = name.split(".")[-1]
        if short in _RESERVED or short.startswith("__"):
            continue
        names.append(name)
    return sorted(names)


def validate_module(mod, name):
    """Return (manifest, fns, error). fns maps stage -> callable."""
    m = getattr(mod, "MANIFEST", None)
    if not isinstance(m, dict):
        return None, None, f"{name}: no MANIFEST dict"
    miss = [k for k in _REQUIRED_MANIFEST if not m.get(k)]
    if miss:
        return None, None, f"{name}: manifest missing {miss}"
    stages = m["stages"]
    if not isinstance(stages, list) or not stages or any(s not in STAGES for s in stages):
        return None, None, f"{name}: stages must be a non-empty subset of {STAGES}"
    fns = {}
    for stage in stages:
        fn = getattr(mod, STAGE_FN[stage], None)
        if not callable(fn):
            return None, None, f"{name}: stage '{stage}' requires callable {STAGE_FN[stage]}()"
        fns[stage] = fn
    return m, fns, ""


def load_markets(package="clearstra_markets"):
    """Load, validate, dedup markets. Returns {markets, dropped, errors}."""
    registry = {"markets": {}, "dropped": [], "errors": []}
    seen_fp = {}
    for mod_name in discover_module_names(package):
        try:
            mod = importlib.import_module(f"{package}.{mod_name}")
        except Exception as exc:  # noqa: BLE001
            registry["errors"].append(f"{mod_name}: import failed: {exc}")
            continue
        manifest, fns, err = validate_module(mod, mod_name)
        if err:
            registry["errors"].append(err)
            continue
        fp = fingerprint_market(manifest)
        if fp in seen_fp:
            registry["dropped"].append({"name": manifest["name"],
                                        "reason": f"duplicate_fingerprint_of:{seen_fp[fp]}"})
            continue
        seen_fp[fp] = manifest["name"]
        registry["markets"][manifest["name"]] = {
            **manifest, "fingerprint": fp, "module": f"{package}.{mod_name}",
            "fns": fns, "samples": dict(getattr(mod, "SAMPLES", {})),
        }
    return registry


def get_market(registry, name):
    if name not in registry["markets"]:
        raise KeyError(f"unknown market: {name} (have: {sorted(registry['markets'])})")
    return registry["markets"][name]


def run_stage(market, stage, inputs, now=""):
    """Execute one stage of a market through the kernel. inputs is stage-specific."""
    if stage not in market["fns"]:
        raise ValueError(f"market '{market['name']}' does not implement stage '{stage}'")
    fns = market["fns"]  # keyed by stage name
    if stage == "price":
        return fns["price"](inputs["order"], inputs.get("P", {}))
    if stage == "clear":
        return clear(inputs["pool"], inputs["supply"], priority_key=fns["clear"], now=now)
    if stage == "settle":
        return settle(inputs["contract"], inputs["outcome"], payoff=fns["settle"], now=now)
    if stage == "rehearse":
        return rehearse(inputs["scenario"], inputs["pool"], model=fns["rehearse"], now=now)
    raise ValueError(f"unknown stage: {stage}")

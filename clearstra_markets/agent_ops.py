#!/usr/bin/env python3
"""AgentOpsMarket — agent-operation cost pricing + accountability as a Clearstra market.

source_project: github.com/sadpig70/AgentMesh
stages: price

ROUTING FINDING (HELIX machine-aware routing): the "Compatibility Mesh" cluster shares a
name but not one machine. AgentMesh has NO verdict algebra — its machine is pricing
(units * unit_cost) + accountability role assignment + cost rollup. That is Clearstra's
`price` machine, NOT Attestra's predicate gate. So AgentMesh lands on Clearstra as a
pricing market, completing the cluster's split across three platforms: Attestra
(SovMesh/PqcMesh/SignalMesh gates), Routestra (FlowMesh bound), Clearstra (AgentMesh price).

price() reproduces AgentMesh.price_record (units * COST_TABLE unit_cost) and
account.assign_role. The per-operator/role/op_type rollup is a report over many priced
orders, above the per-order kernel stage. See tests/test_agent_ops_parity.py.
"""

from ._base import require_non_negative

# Indicative unit cost per operation concern (mirror AgentMesh.models.COST_TABLE).
COST_TABLE = {
    "memory": (0.0000004, "tokens"),
    "tool": (0.002, "tool_calls"),
    "cost": (1.0, "usd"),
    "rollback": (1.5, "rollbacks"),
}

# Accountable operations role per concern (mirror AgentMesh.models.ROLE_TABLE).
ROLE_TABLE = {
    "memory": "memory-steward",
    "tool": "tool-operator",
    "cost": "finops-owner",
    "rollback": "incident-commander",
}
UNASSIGNED_ROLE = "unassigned-operator"


def price(order, P=None):
    """cost = units * unit_cost(op_type); role = ROLE_TABLE[op_type].

    Mirrors AgentMesh.price_record + account.assign_role. An unrecognized op_type
    prices to 0.0 and is assigned the unassigned-operator role (source behavior).
    """
    op_type = str(order.get("op_type", ""))
    units = order.get("units", 0)
    require_non_negative("units", units)
    coeff = COST_TABLE.get(op_type)
    unit_cost, unit_kind = coeff if coeff is not None else (0.0, "unknown")
    cost = units * unit_cost
    return {
        "op_type": op_type,
        "units": units,
        "unit_cost": unit_cost,
        "unit_kind": unit_kind,
        "cost": cost,
        "accountable_role": ROLE_TABLE.get(op_type, UNASSIGNED_ROLE),
    }


MANIFEST = {
    "name": "agent-ops", "version": "1.0", "stages": ["price"],
    "order_schema": "schemas/order-agentops.schema.json",
    "source_project": "github.com/sadpig70/AgentMesh",
}

SAMPLES = {
    # 1000 tool calls * $0.002 = $2.00, accountable to tool-operator
    "price": {"order": {"op_type": "tool", "units": 1000, "operator": "acme", "agent_id": "a1"}},
}

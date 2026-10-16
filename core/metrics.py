"""
core/metrics.py
===============
Role A — Fairness & Performance Metrics for Fest Ops

Public functions
----------------
allocation_efficiency(obtained_utility, max_utility) -> float
fairness_index(allocations) -> float
resource_utilization(allocated_count, total_count) -> float
recovery_time(events, disruption_round, resource_id, committee_id) -> int | None

All functions handle edge cases (empty lists, zeros) without raising exceptions.

Role D's Simulator calls these after every round to populate the metrics DataFrame.
Role C's baseline.py also calls allocation_efficiency() to compare decentralized vs
centralised optimal utility.
"""

from __future__ import annotations

from typing import Sequence


# ---------------------------------------------------------------------------
# 1. Allocation Efficiency
# ---------------------------------------------------------------------------

def allocation_efficiency(obtained_utility: float, max_utility: float) -> float:
    
    if max_utility <= 0:
        return 0.0

    # Clamp to [0, 1] to handle floating-point overshoot
    efficiency = obtained_utility / max_utility
    return max(0.0, min(1.0, efficiency))


# ---------------------------------------------------------------------------
# 2. Jain's Fairness Index
# ---------------------------------------------------------------------------

def fairness_index(allocations: Sequence[float]) -> float:
    
    if len(allocations) == 0:
        # No committees → vacuously fair
        return 1.0

    n = len(allocations)
    total = sum(allocations)
    sum_sq = sum(x * x for x in allocations)

    if sum_sq == 0:
        # All utilities are zero → everyone is equally at zero → perfectly fair
        return 1.0

    return (total ** 2) / (n * sum_sq)


# ---------------------------------------------------------------------------
# 3. Resource Utilisation
# ---------------------------------------------------------------------------

def resource_utilization(allocated_count: int, total_count: int) -> float:
    
    if total_count <= 0:
        return 0.0

    ratio = allocated_count / total_count
    return max(0.0, min(1.0, ratio))


# ---------------------------------------------------------------------------
# 4. Recovery Time
# ---------------------------------------------------------------------------

def recovery_time(
    events: list[dict],
    disruption_round: int,
    resource_id: str,
    committee_id: str,
) -> int | None:
    
    for event in events:
        if (
            event.get("event") == "reallocated"
            and event.get("resource_id") == resource_id
            and event.get("committee_id") == committee_id
            and event.get("round", -1) > disruption_round
        ):
            return event["round"] - disruption_round

    # No recovery found yet
    return None

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
    """
    Compute how efficiently the auction allocated resources.

    Formula
    -------
    efficiency = obtained_utility / max_utility

    Returns a value in [0.0, 1.0].

    Parameters
    ----------
    obtained_utility : float
        Sum of utilities actually received by all committees after allocation.
    max_utility : float
        The theoretical maximum utility (e.g. from the centralised Hungarian
        baseline computed by Role C).

    Returns
    -------
    float
        Efficiency score in [0.0, 1.0].
        Returns 0.0 if max_utility is zero or negative.
        Returns 1.0 if obtained_utility >= max_utility (clamps at 1.0).

    Examples
    --------
    >>> allocation_efficiency(750, 1000)
    0.75
    >>> allocation_efficiency(0, 0)
    0.0
    """
    if max_utility <= 0:
        return 0.0

    # Clamp to [0, 1] to handle floating-point overshoot
    efficiency = obtained_utility / max_utility
    return max(0.0, min(1.0, efficiency))


# ---------------------------------------------------------------------------
# 2. Jain's Fairness Index
# ---------------------------------------------------------------------------

def fairness_index(allocations: Sequence[float]) -> float:
    """
    Compute Jain's Fairness Index over a list of per-committee utility values.

    Formula
    -------
    J = (Σ xᵢ)²  /  (n · Σ xᵢ²)

    where n = number of committees, xᵢ = utility of committee i.

    Returns a value in (0.0, 1.0].
    J = 1.0 means perfectly equal allocation.
    J → 1/n means maximally unequal (one committee gets everything).

    Special cases
    -------------
    - Empty list → returns 1.0  (vacuously fair; document this interpretation)
    - All zeros  → returns 1.0  (all committees equally at zero; no unfairness)

    Parameters
    ----------
    allocations : Sequence[float]
        Per-committee utility or budget-spent values.

    Returns
    -------
    float
        Jain's fairness index in (0.0, 1.0].

    Examples
    --------
    >>> fairness_index([100, 100, 100, 100])
    1.0
    >>> fairness_index([0, 0, 0])
    1.0
    >>> round(fairness_index([1000, 0, 0, 0]), 4)
    0.25
    """
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
    """
    Fraction of available resources that were successfully allocated.

    Formula
    -------
    utilization = allocated_count / total_count

    Returns a value in [0.0, 1.0].

    Parameters
    ----------
    allocated_count : int
        Number of resources that were allocated to at least one committee.
    total_count : int
        Total number of resources available in the pool.

    Returns
    -------
    float
        Utilization rate in [0.0, 1.0].
        Returns 0.0 if total_count == 0.

    Examples
    --------
    >>> resource_utilization(4, 6)
    0.6666666666666666
    >>> resource_utilization(0, 0)
    0.0
    """
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
    """
    How many rounds it took for a committee to recover after a disruption.

    Recovery is defined as a "reallocated" event for the same (resource_id,
    committee_id) pair that occurs *after* disruption_round.

    Expected event format
    ---------------------
    Each element of `events` is a dict with at least these keys:

        {
            "round":        int,   # simulation round number
            "event":        str,   # "disruption" | "reallocated" | other
            "resource_id":  str,   # which resource
            "committee_id": str    # which committee
        }

    Parameters
    ----------
    events : list[dict]
        Ordered list of simulation event records (produced by Role D's Simulator).
    disruption_round : int
        The round in which the disruption was first recorded.
    resource_id : str
        The disrupted resource's ID.
    committee_id : str
        The committee that lost the resource and needs to recover.

    Returns
    -------
    int | None
        Number of rounds between disruption and successful reallocation.
        Returns None if no recovery event is found in `events`.

    Examples
    --------
    >>> events = [
    ...     {"round": 3, "event": "disruption",  "resource_id": "sound_system_A", "committee_id": "cultural_night"},
    ...     {"round": 5, "event": "reallocated", "resource_id": "sound_system_A", "committee_id": "cultural_night"},
    ... ]
    >>> recovery_time(events, 3, "sound_system_A", "cultural_night")
    2
    """
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

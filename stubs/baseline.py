"""
stubs/baseline.py
=================
TEMPORARY STUB — Standing in for Role C's `core/baseline.py`
Computes the theoretical optimal resource allocation using the Hungarian Algorithm
(scipy.optimize.linear_sum_assignment) for centralized comparison.

SWAP NOTICE:
Once Role C's code lands, replace imports with:
    from core.baseline import compute_hungarian_baseline
"""

from __future__ import annotations

from typing import Any
import numpy as np
from scipy.optimize import linear_sum_assignment


def compute_hungarian_baseline(
    committees: list[Any],
    resources: list[dict | str | Any],
) -> tuple[float, dict[str, str]]:
    """
    Compute the centralized theoretical maximum utility using the Hungarian Algorithm.

    Parameters
    ----------
    committees : list[CommitteeAgent]
        List of committee agents (each implements compute_valuation(resource)).
    resources : list[dict | str | Any]
        List of available resources.

    Returns
    -------
    tuple[float, dict[str, str]]
        - Total maximum utility achievable under central planner.
        - Mapping of {resource_id: committee_id}.
    """
    if not committees or not resources:
        return 0.0, {}

    res_ids: list[str] = [
        r["id"] if isinstance(r, dict) else str(getattr(r, "id", r))
        for r in resources
    ]

    # Build utility matrix (committees x resources)
    n_c = len(committees)
    n_r = len(res_ids)
    utility_matrix = np.zeros((n_c, n_r))

    for i, c in enumerate(committees):
        for j, res_id in enumerate(res_ids):
            # Only consider resources the committee actually wants
            wanted = getattr(c, "wanted_resources", [])
            substitutes = getattr(c, "substitutes", {})
            all_acceptable = set(wanted)
            for subs in substitutes.values():
                all_acceptable.update(subs)

            if res_id in all_acceptable:
                utility_matrix[i, j] = c.compute_valuation({"id": res_id})
            else:
                utility_matrix[i, j] = 0.0

    # Hungarian algorithm minimizes cost, so we minimize negative utility
    cost_matrix = -utility_matrix
    row_ind, col_ind = linear_sum_assignment(cost_matrix)

    max_utility = float(utility_matrix[row_ind, col_ind].sum())
    assignment: dict[str, str] = {}
    for r, c in zip(row_ind, col_ind):
        if utility_matrix[r, c] > 0:
            assignment[res_ids[c]] = committees[r].id

    return max_utility, assignment

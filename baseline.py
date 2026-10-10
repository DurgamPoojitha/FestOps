from __future__ import annotations

from typing import Any
import numpy as np
from scipy.optimize import linear_sum_assignment


def _get_resource_id(resource: dict | str | Any) -> str:
    """Return a resource ID from a dict, object, or string."""
    if isinstance(resource, dict):
        return str(resource["id"])
    return str(getattr(resource, "id", resource))


def build_utility_matrix(
    committees: list[Any],
    resources: list[dict | str | Any],
) -> np.ndarray:
    """
    Build the committee × resource utility matrix.

    Only resources that a committee wants or accepts as substitutes
    receive a positive valuation.
    """
    n_committees = len(committees)
    n_resources = len(resources)

    utility_matrix = np.zeros((n_committees, n_resources))

    for i, committee in enumerate(committees):
        wanted = getattr(committee, "wanted_resources", [])
        substitutes = getattr(committee, "substitutes", {})

        all_acceptable = set(wanted)

        for subs in substitutes.values():
            all_acceptable.update(subs)

        for j, resource in enumerate(resources):
            resource_id = _get_resource_id(resource)

            if resource_id in all_acceptable:
                utility_matrix[i, j] = committee.compute_valuation(
                    {"id": resource_id}
                )

    return utility_matrix


def compute_hungarian_baseline(
    committees: list[Any],
    resources: list[dict | str | Any],
) -> tuple[float, dict[str, str]]:
    """
    Compute the centralized theoretical maximum utility
    using the Hungarian Algorithm.

    Returns:
        tuple:
            max_utility: Maximum total utility.
            assignment: Mapping of {resource_id: committee_id}.
    """
    if not committees or not resources:
        return 0.0, {}

    utility_matrix = build_utility_matrix(committees, resources)

    # Hungarian algorithm minimizes cost,
    # so negate utility to maximize it.
    cost_matrix = -utility_matrix

    row_ind, col_ind = linear_sum_assignment(cost_matrix)

    max_utility = float(
        utility_matrix[row_ind, col_ind].sum()
    )

    assignment: dict[str, str] = {}

    for row, col in zip(row_ind, col_ind):
        utility = utility_matrix[row, col]

        if utility > 0:
            resource_id = _get_resource_id(resources[col])
            committee_id = str(committees[row].id)
            assignment[resource_id] = committee_id

    return max_utility, assignment
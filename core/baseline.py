from typing import Any

import numpy as np
from scipy.optimize import linear_sum_assignment


def build_utility_matrix(
    committees: list[Any],
    resources: list[dict | Any],
) -> np.ndarray:
    """
    Build a matrix where each row represents a committee
    and each column represents a resource.

    The utility is calculated using the CommitteeAgent's
    compute_valuation() method.
    """
    matrix = np.zeros((len(committees), len(resources)), dtype=float)

    for i, committee in enumerate(committees):
        for j, resource in enumerate(resources):
            matrix[i, j] = committee.compute_valuation(resource)

    return matrix


def compute_hungarian_baseline(
    committees: list[Any],
    resources: list[dict | Any],
) -> dict[str, Any]:
    """
    Compute the centralized optimal assignment using
    the Hungarian algorithm.

    Returns:
        assignment: list of committee/resource assignments
        total_utility: total utility of the assignment
        efficiency: normalized efficiency percentage
        utility_matrix: matrix used for the calculation
    """
    if not committees or not resources:
        return {
            "assignment": [],
            "total_utility": 0.0,
            "efficiency": 0.0,
            "utility_matrix": np.zeros(
                (len(committees), len(resources)),
                dtype=float,
            ),
        }

    utility_matrix = build_utility_matrix(committees, resources)

    # linear_sum_assignment minimizes cost, so negate utilities
    row_indices, col_indices = linear_sum_assignment(-utility_matrix)

    assignment = []

    for row, col in zip(row_indices, col_indices):
        committee_id = committees[row].id

        resource = resources[col]
        if isinstance(resource, dict):
            resource_id = resource["id"]
        else:
            resource_id = resource.id

        utility = float(utility_matrix[row, col])

        assignment.append(
            {
                "committee_id": committee_id,
                "resource_id": resource_id,
                "utility": utility,
            }
        )

    total_utility = sum(item["utility"] for item in assignment)

    max_possible = float(
        np.max(utility_matrix, axis=1).sum()
    )

    efficiency = (
        (total_utility / max_possible) * 100
        if max_possible > 0
        else 0.0
    )

    return {
        "assignment": assignment,
        "total_utility": total_utility,
        "efficiency": efficiency,
        "utility_matrix": utility_matrix,
    }
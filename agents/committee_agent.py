"""
agents/committee_agent.py
=========================
Role A — CommitteeAgent

A CommitteeAgent is a self-interested bidder that represents one college-fest
committee.  It knows its own budget, its priorities, which resources it wants,
and which substitutes it would accept if it loses a primary resource.

Public interface consumed by other roles
----------------------------------------
Role B (Auction):
    bid = committee.generate_bid(resource)   -> Bid

Role C (Baseline):
    utility = committee.compute_valuation(resource)   -> float

Role D (Simulator):
    committee.id
    committee.remaining_budget
    committee.allocated_resources
    committee.partial_fulfillment
    committee.get_state()

Do NOT rename any of the above attributes or methods without updating all roles.
"""

from __future__ import annotations

import random
from typing import Any

from core.messages import Bid


# ---------------------------------------------------------------------------
# Centralised resource-value table
# ---------------------------------------------------------------------------
# Keep ALL base values here.  Do not hard-code numbers anywhere else.
# Role C's baseline.py also reads these to build the utility matrix.

RESOURCE_VALUES: dict[str, float] = {
    "main_auditorium_evening": 1000.0,
    "open_air_theatre_evening": 700.0,
    "sound_system_A": 800.0,
    "projector_A": 500.0,
    "volunteers_10": 400.0,
    "sports_ground": 900.0,
}


# ---------------------------------------------------------------------------
# Private helper
# ---------------------------------------------------------------------------

def _get_resource_id(resource: Any) -> str:
   
    if isinstance(resource, dict):
        if "id" not in resource:
            raise ValueError(f"Resource dict has no 'id' key: {resource}")
        return resource["id"]

    if hasattr(resource, "id"):
        return resource.id

    raise ValueError(
        f"Cannot extract resource ID from {type(resource)!r}. "
        "Expected a dict with key 'id' or an object with attribute 'id'."
    )


# ---------------------------------------------------------------------------
# CommitteeAgent
# ---------------------------------------------------------------------------

class CommitteeAgent:
   

    def __init__(
        self,
        committee_id: str,
        budget: float,
        priorities: dict[str, float],
        wanted_resources: list[str],
        substitutes: dict[str, list[str]],
        rng: random.Random | None = None,
    ) -> None:
        # -- Core identity & financial state ----------------------------------
        self.id: str = committee_id
        self.budget: float = float(budget)
        self.remaining_budget: float = float(budget)

        # -- Strategy & preferences -------------------------------------------
        self.priorities: dict[str, float] = priorities
        self.wanted_resources: list[str] = list(wanted_resources)
        self.substitutes: dict[str, list[str]] = {
            k: list(v) for k, v in substitutes.items()
        }

        # -- Outcome tracking (used by Role D) --------------------------------
        self.allocated_resources: list[str] = []
        self.partial_fulfillment: list[str] = []  # resources not obtained & no substitute

        # -- Randomness (injectable for testing) ------------------------------
        self._rng: random.Random = rng if rng is not None else random.Random()

    # ------------------------------------------------------------------
    # Valuation
    # ------------------------------------------------------------------

    def compute_valuation(self, resource: Any) -> float:
        
        resource_id = _get_resource_id(resource)
        base_value = RESOURCE_VALUES.get(resource_id, 0.0)

        if base_value == 0.0:
            # Unknown resource — no value to this committee
            return 0.0

        # Priority factor: weighted combination of the three priority dimensions
        turnout = self.priorities.get("turnout", 0.0)
        sponsor = self.priorities.get("sponsor_visibility", 0.0)
        sensitivity = self.priorities.get("budget_sensitivity", 0.0)

        # budget_sensitivity measures risk-aversion; *higher* sensitivity →
        # the committee is cautious, so we subtract it from the factor.
        priority_factor = (
            0.5 * turnout
            + 0.3 * sponsor
            + 0.2 * (1.0 - sensitivity)
        )
        # Clamp to [0, 1]
        priority_factor = max(0.0, min(1.0, priority_factor))

        # Budget factor: fraction of the original budget that remains.
        # Full budget → 1.0 (committee bids aggressively).
        # Near-empty budget → 0.1 floor (committee is cautious).
        if self.budget > 0:
            budget_factor = self.remaining_budget / self.budget
        else:
            budget_factor = 0.0
        budget_factor = max(0.1, min(1.0, budget_factor))

        valuation = base_value * priority_factor * budget_factor
        return max(0.0, round(valuation, 2))

    # ------------------------------------------------------------------
    # Bidding
    # ------------------------------------------------------------------

    def generate_bid(self, resource: Any) -> Bid:
        """
        Generate a bid for the given resource.

        Algorithm
        ---------
        1. Compute valuation.
        2. Randomly shade between 85 % and 100 % (bid-shading = strategic under-reveal).
        3. Cap at remaining_budget.
        4. Floor at 0.0.
        5. Round to 2 decimal places.
        6. Return a ``Bid`` dataclass.

        The random generator is injectable (see ``rng`` constructor parameter)
        so tests can pass a seeded ``random.Random`` for reproducibility without
        making the production code deterministic.

        Parameters
        ----------
        resource : dict | object
            The resource being bid on.

        Returns
        -------
        Bid
            The shared ``Bid`` dataclass from ``core.messages``.
        """
        resource_id = _get_resource_id(resource)

        if self.remaining_budget <= 0:
            return Bid(
                committee_id=self.id,
                resource_id=resource_id,
                amount=0.0,
            )

        valuation = self.compute_valuation(resource)

        # Bid shading: bid between 85 % and 100 % of true valuation
        shade = self._rng.uniform(0.85, 1.0)
        bid_amount = valuation * shade

        # Cap at remaining budget; floor at 0
        bid_amount = min(bid_amount, self.remaining_budget)
        bid_amount = max(0.0, bid_amount)

        return Bid(
            committee_id=self.id,
            resource_id=resource_id,
            amount=round(bid_amount, 2),
        )

    # ------------------------------------------------------------------
    # Allocation (called by Role B / Role D after auction)
    # ------------------------------------------------------------------

    def allocate_resource(self, resource_id: str, cost: float) -> None:
        
        if cost < 0:
            raise ValueError(
                f"[{self.id}] Cannot allocate resource with negative cost: {cost}"
            )

        # Clamp to avoid going negative (defensive guard)
        actual_cost = min(cost, self.remaining_budget)
        self.remaining_budget = round(self.remaining_budget - actual_cost, 2)
        self.remaining_budget = max(0.0, self.remaining_budget)

        if resource_id not in self.allocated_resources:
            self.allocated_resources.append(resource_id)

    # ------------------------------------------------------------------
    # Losing an auction (called by Role B / Role D after auction)
    # ------------------------------------------------------------------

    def on_lost_auction(
        self,
        resource: Any,
        available_resources: list[Any] | None = None,
    ) -> dict:
        
        resource_id = _get_resource_id(resource)

        substitute = self.get_next_substitute(resource_id, available_resources)

        if substitute is not None:
            return {"status": "substitute", "resource_id": substitute}

        # No substitute available — log partial fulfillment
        if resource_id not in self.partial_fulfillment:
            self.partial_fulfillment.append(resource_id)

        return {"status": "partial_fulfillment", "resource_id": None}

    # ------------------------------------------------------------------
    # Supporting helpers
    # ------------------------------------------------------------------

    def has_budget(self, amount: float) -> bool:
        """
        Return True if the committee can afford ``amount``.

        Parameters
        ----------
        amount : float
            The cost to check against remaining_budget.
        """
        return self.remaining_budget >= amount

    def get_next_substitute(
        self,
        resource_id: str,
        available_resources: list[Any] | None = None,
    ) -> str | None:
        """
        Return the first viable substitute for ``resource_id``, or None.

        Parameters
        ----------
        resource_id : str
            The primary resource that was not obtained.
        available_resources : list[dict | object] | None
            If provided, only consider substitutes present in this pool.
            If None, return the first listed substitute unconditionally.

        Returns
        -------
        str | None
            The substitute resource ID, or None if none is available.
        """
        substitutes_for = self.substitutes.get(resource_id, [])

        if not substitutes_for:
            return None

        if available_resources is None:
            # No pool provided → return first listed substitute
            return substitutes_for[0]

        # Build a set of available IDs for fast lookup
        available_ids: set[str] = set()
        for r in available_resources:
            try:
                available_ids.add(_get_resource_id(r))
            except ValueError:
                continue

        for sub_id in substitutes_for:
            if sub_id in available_ids:
                return sub_id

        return None

    def get_state(self) -> dict:
        """
        Return a snapshot of this committee's current state.

        This is the primary interface for Role D's Simulator and the Streamlit UI.

        Returns
        -------
        dict
            Keys: id, budget, remaining_budget, priorities, wanted_resources,
                  substitutes, allocated_resources, partial_fulfillment.
        """
        return {
            "id": self.id,
            "budget": self.budget,
            "remaining_budget": self.remaining_budget,
            "priorities": dict(self.priorities),
            "wanted_resources": list(self.wanted_resources),
            "substitutes": {k: list(v) for k, v in self.substitutes.items()},
            "allocated_resources": list(self.allocated_resources),
            "partial_fulfillment": list(self.partial_fulfillment),
        }

    def __repr__(self) -> str:
        return (
            f"CommitteeAgent(id={self.id!r}, "
            f"budget={self.budget}, "
            f"remaining={self.remaining_budget})"
        )

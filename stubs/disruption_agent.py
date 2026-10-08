"""
stubs/disruption_agent.py
=========================
TEMPORARY STUB — Standing in for Role C's `agents/disruption_agent.py`
This mock implementation allows Role D (Simulator & Demo) to build and run
end-to-end without waiting for Role C's branch to merge.

SWAP NOTICE:
Once Role C's code lands, replace imports of this class with:
    from agents.disruption_agent import DisruptionAgent
"""

from __future__ import annotations

import random
from typing import Sequence

from core.messages import DisruptionEvent

DISRUPTION_REASONS = [
    "equipment_failure",
    "venue_unavailable",
    "volunteer_dropout",
]


class DisruptionAgent:
    """
    Mock DisruptionAgent standing in for Role C.

    Injects random or forced disruptions into the simulation environment
    to test the decentralized multi-agent recovery mechanism.
    """

    def __init__(
        self,
        probability: float = 0.0,
        rng: random.Random | None = None,
    ) -> None:
        """
        Parameters
        ----------
        probability : float
            Probability [0.0, 1.0] of a disruption occurring during `maybe_trigger`.
        rng : random.Random | None
            Injectable RNG for deterministic testing.
        """
        self.probability: float = max(0.0, min(1.0, float(probability)))
        self._rng: random.Random = rng if rng is not None else random.Random()
        self.disruption_history: list[DisruptionEvent] = []

    def maybe_trigger(
        self,
        round_num: int,
        targetable_resources: Sequence[str] | None = None,
    ) -> DisruptionEvent | None:
        """
        Stochastically trigger a disruption event based on configured probability.

        Parameters
        ----------
        round_num : int
            Current simulation round number.
        targetable_resources : Sequence[str] | None
            List of resource IDs currently allocated and eligible for disruption.
            If None or empty, disruptions cannot target active resources.

        Returns
        -------
        DisruptionEvent | None
            A disruption event if triggered, else None.
        """
        if self.probability <= 0.0 or not targetable_resources:
            return None

        roll = self._rng.random()
        if roll < self.probability:
            target_res = self._rng.choice(list(targetable_resources))
            reason = self._rng.choice(DISRUPTION_REASONS)
            event = DisruptionEvent(
                round_num=round_num,
                resource_id=target_res,
                reason=reason,
            )
            self.disruption_history.append(event)
            return event

        return None

    def force_trigger(
        self,
        resource_id: str | None = None,
        round_num: int = 1,
        fallback_resources: Sequence[str] | None = None,
    ) -> DisruptionEvent:
        """
        Deterministically trigger a disruption event (for live demo or test cases).

        Parameters
        ----------
        resource_id : str | None
            The specific resource ID to disrupt. If None, picks from fallback_resources
            or defaults to 'sound_system_A'.
        round_num : int
            Simulation round number.
        fallback_resources : Sequence[str] | None
            Pool of resources to pick from if resource_id is None.

        Returns
        -------
        DisruptionEvent
            The forced disruption event.
        """
        if resource_id is None:
            if fallback_resources:
                target_res = self._rng.choice(list(fallback_resources))
            else:
                target_res = "sound_system_A"
        else:
            target_res = resource_id

        reason = self._rng.choice(DISRUPTION_REASONS)
        event = DisruptionEvent(
            round_num=round_num,
            resource_id=target_res,
            reason=reason,
        )
        self.disruption_history.append(event)
        return event

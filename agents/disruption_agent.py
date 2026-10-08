"""
agents/disruption_agent.py
==========================
Role C — DisruptionAgent responsible for introducing stochastic and forced disruptions.
"""

from __future__ import annotations

import random
from typing import Any

from core.messages import DisruptionEvent


class DisruptionAgent:
    """
    Role C agent responsible for introducing disruptions
    and identifying the affected resource.
    """

    def __init__(
        self,
        probability: float = 0.1,
        seed: int | None = None,
        rng: random.Random | None = None,
    ) -> None:
        self.probability = max(0.0, min(1.0, float(probability)))
        if rng is not None:
            self.rng = rng
        else:
            self.rng = random.Random(seed)

        self.disruption_reasons = [
            "equipment_failure",
            "venue_unavailable",
            "volunteer_dropout",
        ]

        self.events: list[DisruptionEvent] = []

    def maybe_trigger(
        self,
        round_num: int,
        targetable_resources: list[dict | Any] | None = None,
    ) -> DisruptionEvent | None:
        """
        Randomly trigger a disruption according to the configured
        probability. Only currently targetable resources are considered.
        """
        if targetable_resources is None or not targetable_resources:
            return None

        if self.rng.random() >= self.probability:
            return None

        resource = self.rng.choice(targetable_resources)

        if isinstance(resource, dict):
            resource_id = resource["id"]
        elif hasattr(resource, "id"):
            resource_id = resource.id
        else:
            resource_id = str(resource)

        reason = self.rng.choice(self.disruption_reasons)

        event = DisruptionEvent(
            round_num=round_num,
            resource_id=resource_id,
            reason=reason,
        )

        self.events.append(event)
        return event

    def force_trigger(
        self,
        resource_id: str | None = None,
        round_num: int = 0,
        reason: str = "equipment_failure",
        fallback_resources: list[Any] | None = None,
    ) -> DisruptionEvent:
        """
        Manually trigger a disruption for a specific resource.
        Useful for the Streamlit demo.
        """
        valid_reasons = {
            "equipment_failure",
            "venue_unavailable",
            "volunteer_dropout",
        }

        if reason not in valid_reasons:
            raise ValueError(f"Invalid disruption reason: {reason}")

        target_res = resource_id
        if target_res is None:
            if fallback_resources:
                chosen = self.rng.choice(fallback_resources)
                target_res = chosen["id"] if isinstance(chosen, dict) else getattr(chosen, "id", str(chosen))
            else:
                target_res = "sound_system_A"

        event = DisruptionEvent(
            round_num=round_num,
            resource_id=target_res,
            reason=reason,
        )

        self.events.append(event)
        return event

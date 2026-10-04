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
    ) -> None:
        self.probability = max(0.0, min(1.0, probability))
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
        resources: list[dict | Any] | None = None,
    ) -> DisruptionEvent | None:
        """
        Randomly trigger a disruption according to the configured
        probability.

        If a disruption occurs, one resource is selected and a
        DisruptionEvent is returned.
        """
        if resources is None or not resources:
            return None

        if self.rng.random() >= self.probability:
            return None

        resource = self.rng.choice(resources)

        if isinstance(resource, dict):
            resource_id = resource["id"]
        else:
            resource_id = resource.id

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
        resource_id: str,
        round_num: int = 0,
        reason: str = "equipment_failure",
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
            raise ValueError(
                f"Invalid disruption reason: {reason}"
            )

        event = DisruptionEvent(
            round_num=round_num,
            resource_id=resource_id,
            reason=reason,
        )

        self.events.append(event)

        return event
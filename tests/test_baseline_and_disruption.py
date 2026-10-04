import pytest

from agents.committee_agent import CommitteeAgent
from agents.disruption_agent import DisruptionAgent
from core.baseline import compute_hungarian_baseline
from core.messages import DisruptionEvent


def make_committee(committee_id: str, budget: float = 5000.0):
    return CommitteeAgent(
        committee_id=committee_id,
        budget=budget,
        priorities={
            "turnout": 0.8,
            "sponsor_visibility": 0.7,
            "budget_sensitivity": 0.5,
        },
        wanted_resources=[],
        substitutes={},
    )


def test_hungarian_baseline_small_example():
    committees = [
        make_committee("C1"),
        make_committee("C2"),
    ]

    resources = [
        {"id": "R1"},
        {"id": "R2"},
    ]

    result = compute_hungarian_baseline(
        committees,
        resources,
    )

    assert len(result["assignment"]) == 2
    assert result["total_utility"] >= 0
    assert 0 <= result["efficiency"] <= 100


def test_forced_disruption():
    agent = DisruptionAgent(seed=42)

    event = agent.force_trigger(
        resource_id="R1",
        round_num=1,
    )

    assert isinstance(event, DisruptionEvent)
    assert event.round_num == 1
    assert event.resource_id == "R1"
    assert event.reason == "equipment_failure"
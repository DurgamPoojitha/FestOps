from agents.committee_agent import CommitteeAgent
from agents.disruption_agent import DisruptionAgent
from core.baseline import compute_hungarian_baseline
from core.messages import DisruptionEvent


def make_committee(committee_id, wanted_resources):
    return CommitteeAgent(
        committee_id=committee_id,
        budget=5000,
        priorities={
            "turnout": 0.8,
            "sponsor_visibility": 0.7,
            "budget_sensitivity": 0.5,
        },
        wanted_resources=wanted_resources,
        substitutes={},
    )


def test_hungarian_baseline_small_example():
    committees = [
        make_committee("C1", ["main_auditorium_evening"]),
        make_committee("C2", ["sports_ground"]),
    ]

    resources = [
        {"id": "main_auditorium_evening"},
        {"id": "sports_ground"},
    ]

    max_utility, assignment = compute_hungarian_baseline(
        committees,
        resources,
    )

    assert assignment == {
        "main_auditorium_evening": "C1",
        "sports_ground": "C2",
    }

    assert max_utility == 1349.0


def test_forced_disruption():
    agent = DisruptionAgent(seed=42)

    event = agent.force_trigger(
        resource_id="main_auditorium_evening",
        round_num=1,
    )

    assert isinstance(event, DisruptionEvent)
    assert event.round_num == 1
    assert event.resource_id == "main_auditorium_evening"
    assert event.reason == "equipment_failure"
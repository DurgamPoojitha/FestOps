"""
tests/test_committee_agent.py
==============================
Role A — Comprehensive pytest test suite for CommitteeAgent and metrics.

Test coverage (15 tests required by spec)
-----------------------------------------
 1. test_committee_initialization
 2. test_valuation_is_deterministic
 3. test_different_committees_have_different_valuations
 4. test_bid_is_within_85_to_100_percent_of_valuation
 5. test_bid_never_exceeds_budget
 6. test_zero_budget_generates_zero_bid
 7. test_winner_allocation_reduces_budget
 8. test_budget_never_goes_negative
 9. test_loser_pays_nothing
10. test_substitute_selected_after_loss
11. test_partial_fulfillment_when_no_substitute
12. test_jain_fairness_equal_allocations
13. test_jain_fairness_zero_allocations
14. test_resource_utilization
15. test_recovery_time

Run with:
    pytest tests/test_committee_agent.py -v
"""

from __future__ import annotations

import random
import sys
import os

# Make sure the project root is on the Python path so imports work whether
# pytest is run from the project root or from inside tests/.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from agents.committee_agent import CommitteeAgent, RESOURCE_VALUES
from core.messages import Bid
from core.metrics import (
    allocation_efficiency,
    fairness_index,
    recovery_time,
    resource_utilization,
)


# ---------------------------------------------------------------------------
# Fixtures — reusable test objects
# ---------------------------------------------------------------------------

CULTURAL_NIGHT_CONFIG = {
    "committee_id": "cultural_night",
    "budget": 1000.0,
    "priorities": {
        "turnout": 0.60,
        "sponsor_visibility": 0.20,
        "budget_sensitivity": 0.20,
    },
    "wanted_resources": ["main_auditorium_evening", "sound_system_A", "volunteers_10"],
    "substitutes": {
        "main_auditorium_evening": ["open_air_theatre_evening"],
    },
}

TECHNICAL_FEST_CONFIG = {
    "committee_id": "technical_fest",
    "budget": 800.0,
    "priorities": {
        "turnout": 0.30,
        "sponsor_visibility": 0.50,
        "budget_sensitivity": 0.20,
    },
    "wanted_resources": ["main_auditorium_evening", "projector_A", "volunteers_10"],
    "substitutes": {
        "main_auditorium_evening": ["open_air_theatre_evening"],
    },
}

# Sample resources as dicts (the standard format from resources.yaml)
RESOURCE_AUDITORIUM = {"id": "main_auditorium_evening", "type": "venue", "capacity": 1}
RESOURCE_OAT = {"id": "open_air_theatre_evening", "type": "venue", "capacity": 1}
RESOURCE_SOUND = {"id": "sound_system_A", "type": "equipment", "capacity": 1}
RESOURCE_PROJECTOR = {"id": "projector_A", "type": "equipment", "capacity": 1}
RESOURCE_UNKNOWN = {"id": "unknown_resource", "type": "other", "capacity": 1}


@pytest.fixture
def cultural_committee() -> CommitteeAgent:
    """Fresh cultural_night CommitteeAgent for each test."""
    return CommitteeAgent(**CULTURAL_NIGHT_CONFIG)


@pytest.fixture
def technical_committee() -> CommitteeAgent:
    """Fresh technical_fest CommitteeAgent for each test."""
    return CommitteeAgent(**TECHNICAL_FEST_CONFIG)


@pytest.fixture
def seeded_committee() -> CommitteeAgent:
    """cultural_night with a seeded RNG for reproducible bid tests."""
    rng = random.Random(42)
    return CommitteeAgent(**CULTURAL_NIGHT_CONFIG, rng=rng)


# ---------------------------------------------------------------------------
# 1. Initialisation
# ---------------------------------------------------------------------------

class TestCommitteeInitialization:
    """Test 1 — CommitteeAgent initialises with correct attribute values."""

    def test_committee_initialization(self, cultural_committee: CommitteeAgent):
        c = cultural_committee
        assert c.id == "cultural_night"
        assert c.budget == 1000.0
        assert c.remaining_budget == 1000.0
        assert c.priorities["turnout"] == pytest.approx(0.60)
        assert c.priorities["sponsor_visibility"] == pytest.approx(0.20)
        assert c.priorities["budget_sensitivity"] == pytest.approx(0.20)
        assert "main_auditorium_evening" in c.wanted_resources
        assert "main_auditorium_evening" in c.substitutes
        assert c.allocated_resources == []
        assert c.partial_fulfillment == []


# ---------------------------------------------------------------------------
# 2. Valuation is deterministic
# ---------------------------------------------------------------------------

class TestValuation:
    """Tests 2 & 3 — compute_valuation behaviour."""

    def test_valuation_is_deterministic(self, cultural_committee: CommitteeAgent):
        """Calling compute_valuation twice with the same inputs yields the same result."""
        v1 = cultural_committee.compute_valuation(RESOURCE_AUDITORIUM)
        v2 = cultural_committee.compute_valuation(RESOURCE_AUDITORIUM)
        assert v1 == v2, "Valuation must be deterministic."

    def test_valuation_is_positive(self, cultural_committee: CommitteeAgent):
        """Valuation must always be non-negative."""
        for resource in [RESOURCE_AUDITORIUM, RESOURCE_SOUND, RESOURCE_PROJECTOR]:
            val = cultural_committee.compute_valuation(resource)
            assert val >= 0.0, f"Negative valuation for {resource}"

    def test_unknown_resource_valuation_is_zero(self, cultural_committee: CommitteeAgent):
        """Resources not in RESOURCE_VALUES get valuation 0.0."""
        val = cultural_committee.compute_valuation(RESOURCE_UNKNOWN)
        assert val == 0.0

    def test_different_committees_have_different_valuations(
        self,
        cultural_committee: CommitteeAgent,
        technical_committee: CommitteeAgent,
    ):
        """
        Test 3 — committees with different priorities produce different valuations
        for the same resource.
        """
        v_cultural = cultural_committee.compute_valuation(RESOURCE_AUDITORIUM)
        v_technical = technical_committee.compute_valuation(RESOURCE_AUDITORIUM)
        # Different priorities → different values (they should not be identical)
        assert v_cultural != v_technical, (
            "Different committees should produce different valuations."
        )

    def test_valuation_uses_remaining_budget(self, cultural_committee: CommitteeAgent):
        """
        Budget factor = remaining_budget / budget, clamped to [0.1, 1.0].
        A committee with full budget values a resource more than one with 20 % left.
        """
        v_full = cultural_committee.compute_valuation(RESOURCE_AUDITORIUM)

        # Spend 80 % of budget → remaining = 200
        cultural_committee.remaining_budget = 200.0
        v_low = cultural_committee.compute_valuation(RESOURCE_AUDITORIUM)

        assert v_low < v_full, (
            "Valuation should be lower when most of the budget is spent."
        )


# ---------------------------------------------------------------------------
# 4 & 5. Bid shading and budget cap
# ---------------------------------------------------------------------------

class TestGenerateBid:
    """Tests 4 & 5 — generate_bid mechanics."""

    def test_bid_is_within_85_to_100_percent_of_valuation(
        self, seeded_committee: CommitteeAgent
    ):
        """
        Test 4 — bid amount must be between 85 % and 100 % of the committee's
        own valuation for the same resource.
        """
        resource = RESOURCE_AUDITORIUM
        valuation = seeded_committee.compute_valuation(resource)

        # Run multiple bids with different seeds to check the range
        for seed in range(50):
            rng = random.Random(seed)
            c = CommitteeAgent(**CULTURAL_NIGHT_CONFIG, rng=rng)
            bid = c.generate_bid(resource)
            low = round(valuation * 0.85, 2)
            high = round(valuation * 1.00, 2)
            assert low <= bid.amount <= high, (
                f"Seed {seed}: bid {bid.amount} outside [{low}, {high}]"
            )

    def test_bid_never_exceeds_budget(self, seeded_committee: CommitteeAgent):
        """Test 5 — bid amount is always ≤ remaining_budget."""
        seeded_committee.remaining_budget = 200.0  # Force tight budget
        for seed in range(30):
            rng = random.Random(seed)
            c = CommitteeAgent(**CULTURAL_NIGHT_CONFIG, rng=rng)
            c.remaining_budget = 200.0
            bid = c.generate_bid(RESOURCE_AUDITORIUM)
            assert bid.amount <= 200.0, (
                f"Seed {seed}: bid {bid.amount} exceeds budget 200.0"
            )

    def test_bid_returns_correct_dataclass(self, seeded_committee: CommitteeAgent):
        """generate_bid must return a Bid dataclass with correct fields."""
        bid = seeded_committee.generate_bid(RESOURCE_AUDITORIUM)
        assert isinstance(bid, Bid)
        assert bid.committee_id == "cultural_night"
        assert bid.resource_id == "main_auditorium_evening"
        assert bid.amount >= 0.0

    def test_zero_budget_generates_zero_bid(self):
        """Test 6 — committee with zero budget must bid 0.0."""
        c = CommitteeAgent(
            committee_id="broke_committee",
            budget=0.0,
            priorities={"turnout": 0.5, "sponsor_visibility": 0.3, "budget_sensitivity": 0.2},
            wanted_resources=["main_auditorium_evening"],
            substitutes={},
        )
        bid = c.generate_bid(RESOURCE_AUDITORIUM)
        assert bid.amount == 0.0, "Zero-budget committee must bid 0.0."

    def test_bid_is_non_negative(self, cultural_committee: CommitteeAgent):
        """Bid amount must never be negative."""
        for seed in range(20):
            rng = random.Random(seed)
            c = CommitteeAgent(**CULTURAL_NIGHT_CONFIG, rng=rng)
            bid = c.generate_bid(RESOURCE_AUDITORIUM)
            assert bid.amount >= 0.0


# ---------------------------------------------------------------------------
# 7 & 8. Allocation and budget safety
# ---------------------------------------------------------------------------

class TestAllocation:
    """Tests 7 & 8 — allocate_resource reduces budget, never below zero."""

    def test_winner_allocation_reduces_budget(self, cultural_committee: CommitteeAgent):
        """Test 7 — winning the auction deducts the cost from remaining_budget."""
        initial = cultural_committee.remaining_budget
        cost = 350.0
        cultural_committee.allocate_resource("main_auditorium_evening", cost)
        assert cultural_committee.remaining_budget == pytest.approx(initial - cost)

    def test_allocation_adds_resource_to_list(self, cultural_committee: CommitteeAgent):
        """Allocated resource appears in allocated_resources."""
        cultural_committee.allocate_resource("sound_system_A", 200.0)
        assert "sound_system_A" in cultural_committee.allocated_resources

    def test_budget_never_goes_negative(self, cultural_committee: CommitteeAgent):
        """Test 8 — remaining_budget floors at 0.0 even if cost > remaining."""
        cultural_committee.remaining_budget = 100.0
        cultural_committee.allocate_resource("main_auditorium_evening", 5000.0)
        assert cultural_committee.remaining_budget >= 0.0

    def test_invalid_negative_cost_raises(self, cultural_committee: CommitteeAgent):
        """allocate_resource must reject negative costs."""
        with pytest.raises(ValueError):
            cultural_committee.allocate_resource("main_auditorium_evening", -50.0)

    def test_no_duplicate_in_allocated_list(self, cultural_committee: CommitteeAgent):
        """Allocating the same resource twice does not duplicate the list entry."""
        cultural_committee.allocate_resource("sound_system_A", 100.0)
        cultural_committee.allocate_resource("sound_system_A", 0.0)
        assert cultural_committee.allocated_resources.count("sound_system_A") == 1


# ---------------------------------------------------------------------------
# 9. Losing an auction — loser pays nothing
# ---------------------------------------------------------------------------

class TestLossHandling:
    """Tests 9, 10, 11 — on_lost_auction behaviour."""

    def test_loser_pays_nothing(self, cultural_committee: CommitteeAgent):
        """Test 9 — losing an auction does NOT deduct from remaining_budget."""
        budget_before = cultural_committee.remaining_budget
        cultural_committee.on_lost_auction(RESOURCE_AUDITORIUM)
        assert cultural_committee.remaining_budget == pytest.approx(budget_before), (
            "Loser must not lose any money."
        )

    def test_substitute_selected_after_loss(self, cultural_committee: CommitteeAgent):
        """
        Test 10 — when cultural_night loses main_auditorium_evening,
        it should fall back to open_air_theatre_evening.
        """
        result = cultural_committee.on_lost_auction(RESOURCE_AUDITORIUM)
        assert result["status"] == "substitute"
        assert result["resource_id"] == "open_air_theatre_evening"

    def test_substitute_selected_from_available_pool(self, cultural_committee: CommitteeAgent):
        """Substitute is only chosen if it appears in the available pool."""
        # Pool contains the substitute
        pool = [RESOURCE_OAT, RESOURCE_SOUND]
        result = cultural_committee.on_lost_auction(RESOURCE_AUDITORIUM, available_resources=pool)
        assert result["status"] == "substitute"
        assert result["resource_id"] == "open_air_theatre_evening"

    def test_no_substitute_when_pool_excludes_it(self, cultural_committee: CommitteeAgent):
        """When the substitute is not in the available pool, partial fulfillment results."""
        # Pool does NOT contain the substitute
        pool = [RESOURCE_SOUND]
        result = cultural_committee.on_lost_auction(RESOURCE_AUDITORIUM, available_resources=pool)
        assert result["status"] == "partial_fulfillment"
        assert "main_auditorium_evening" in cultural_committee.partial_fulfillment

    def test_partial_fulfillment_when_no_substitute(self, cultural_committee: CommitteeAgent):
        """
        Test 11 — losing sound_system_A (no substitute listed) records
        partial fulfillment.
        """
        result = cultural_committee.on_lost_auction(RESOURCE_SOUND)
        assert result["status"] == "partial_fulfillment"
        assert result["resource_id"] is None
        assert "sound_system_A" in cultural_committee.partial_fulfillment


# ---------------------------------------------------------------------------
# 12 & 13. Jain's Fairness Index
# ---------------------------------------------------------------------------

class TestFairnessIndex:
    """Tests 12 & 13 — fairness_index edge cases and correctness."""

    def test_jain_fairness_equal_allocations(self):
        """Test 12 — equal allocations must yield fairness_index == 1.0."""
        result = fairness_index([100, 100, 100, 100])
        assert result == pytest.approx(1.0), (
            "Jain index must be 1.0 for perfectly equal allocations."
        )

    def test_jain_fairness_zero_allocations(self):
        """Test 13 — all-zero allocations must not raise an error and return 1.0."""
        result = fairness_index([0, 0, 0])
        assert result == pytest.approx(1.0), (
            "All-zero allocations are vacuously fair; expected 1.0."
        )

    def test_jain_fairness_empty_list(self):
        """Empty list must return 1.0 without errors."""
        result = fairness_index([])
        assert result == pytest.approx(1.0)

    def test_jain_fairness_single_winner(self):
        """One committee gets everything → fairness index == 1/n."""
        # [1000, 0, 0, 0]: formula gives (1000)^2 / (4 * 1000^2) = 1/4 = 0.25
        result = fairness_index([1000, 0, 0, 0])
        assert result == pytest.approx(0.25)

    def test_jain_fairness_range(self):
        """Fairness index is always in (0, 1]."""
        for allocations in [[10, 20, 30], [500, 500], [1, 1, 1, 1, 100]]:
            result = fairness_index(allocations)
            assert 0.0 < result <= 1.0, f"Out of range for {allocations}: {result}"

    def test_jain_fairness_single_element(self):
        """Single element → fairness index is 1.0 (trivially fair)."""
        result = fairness_index([500])
        assert result == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# 14. Resource Utilization
# ---------------------------------------------------------------------------

class TestResourceUtilization:
    """Test 14 — resource_utilization correctness."""

    def test_resource_utilization(self):
        """Basic usage: 4 out of 6 resources allocated → 0.667."""
        result = resource_utilization(4, 6)
        assert result == pytest.approx(4 / 6)

    def test_resource_utilization_full(self):
        """All resources allocated → 1.0."""
        assert resource_utilization(6, 6) == pytest.approx(1.0)

    def test_resource_utilization_none(self):
        """Nothing allocated → 0.0."""
        assert resource_utilization(0, 6) == pytest.approx(0.0)

    def test_resource_utilization_zero_total(self):
        """Total == 0 → return 0.0 safely (no division by zero)."""
        result = resource_utilization(0, 0)
        assert result == pytest.approx(0.0)

    def test_resource_utilization_clamped(self):
        """Result is always between 0 and 1."""
        assert 0.0 <= resource_utilization(3, 10) <= 1.0


# ---------------------------------------------------------------------------
# 15. Recovery Time
# ---------------------------------------------------------------------------

class TestRecoveryTime:
    """Test 15 — recovery_time calculation."""

    SAMPLE_EVENTS = [
        {
            "round": 3,
            "event": "disruption",
            "resource_id": "sound_system_A",
            "committee_id": "cultural_night",
        },
        {
            "round": 5,
            "event": "reallocated",
            "resource_id": "sound_system_A",
            "committee_id": "cultural_night",
        },
    ]

    def test_recovery_time(self):
        """Test 15 — basic recovery from round 3 to round 5 → 2 rounds."""
        result = recovery_time(
            self.SAMPLE_EVENTS,
            disruption_round=3,
            resource_id="sound_system_A",
            committee_id="cultural_night",
        )
        assert result == 2

    def test_recovery_time_no_recovery(self):
        """If no reallocation event exists, return None."""
        events = [
            {
                "round": 3,
                "event": "disruption",
                "resource_id": "sound_system_A",
                "committee_id": "cultural_night",
            }
        ]
        result = recovery_time(
            events,
            disruption_round=3,
            resource_id="sound_system_A",
            committee_id="cultural_night",
        )
        assert result is None

    def test_recovery_time_empty_events(self):
        """Empty events list → return None without errors."""
        result = recovery_time([], 1, "sound_system_A", "cultural_night")
        assert result is None

    def test_recovery_time_ignores_earlier_rounds(self):
        """Reallocation events before disruption_round must be ignored."""
        events = [
            {
                "round": 1,
                "event": "reallocated",
                "resource_id": "sound_system_A",
                "committee_id": "cultural_night",
            },
            {
                "round": 5,
                "event": "reallocated",
                "resource_id": "sound_system_A",
                "committee_id": "cultural_night",
            },
        ]
        # disruption at round 3 → only the round-5 event counts
        result = recovery_time(events, 3, "sound_system_A", "cultural_night")
        assert result == 2

    def test_recovery_time_wrong_resource(self):
        """Events for a different resource_id are ignored."""
        events = [
            {
                "round": 5,
                "event": "reallocated",
                "resource_id": "projector_A",   # different resource!
                "committee_id": "cultural_night",
            }
        ]
        result = recovery_time(events, 3, "sound_system_A", "cultural_night")
        assert result is None


# ---------------------------------------------------------------------------
# Allocation Efficiency
# ---------------------------------------------------------------------------

class TestAllocationEfficiency:
    """Extra — allocation_efficiency edge cases."""

    def test_basic_efficiency(self):
        assert allocation_efficiency(750, 1000) == pytest.approx(0.75)

    def test_perfect_efficiency(self):
        assert allocation_efficiency(1000, 1000) == pytest.approx(1.0)

    def test_zero_obtained(self):
        assert allocation_efficiency(0, 1000) == pytest.approx(0.0)

    def test_zero_max_returns_zero(self):
        """Zero max utility → return 0.0 safely."""
        assert allocation_efficiency(0, 0) == pytest.approx(0.0)

    def test_efficiency_clamped_at_one(self):
        """Result is always ≤ 1.0."""
        assert allocation_efficiency(1200, 1000) == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# get_state
# ---------------------------------------------------------------------------

class TestGetState:
    """Verify the get_state snapshot used by Role D."""

    def test_get_state_keys(self, cultural_committee: CommitteeAgent):
        state = cultural_committee.get_state()
        expected_keys = {
            "id",
            "budget",
            "remaining_budget",
            "priorities",
            "wanted_resources",
            "substitutes",
            "allocated_resources",
            "partial_fulfillment",
        }
        assert expected_keys.issubset(set(state.keys()))

    def test_get_state_values_match_attributes(self, cultural_committee: CommitteeAgent):
        cultural_committee.allocate_resource("sound_system_A", 150.0)
        state = cultural_committee.get_state()
        assert state["id"] == cultural_committee.id
        assert state["remaining_budget"] == cultural_committee.remaining_budget
        assert "sound_system_A" in state["allocated_resources"]

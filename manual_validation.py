import pytest
from core.messages import Bid
from agents.committee_agent import CommitteeAgent
from core.metrics import fairness_index

# Scenario 1: One committee, one resource -> valuation, bid
c1 = CommitteeAgent(
    "c1", 1000.0,
    {"turnout": 0.5, "sponsor_visibility": 0.5, "budget_sensitivity": 0},
    ["main_auditorium_evening"], {}
)
r1 = {"id": "main_auditorium_evening"}
val1 = c1.compute_valuation(r1)
bid1 = c1.generate_bid(r1)
print(f"Scenario 1: val={val1}, bid={bid1.amount}")

# Scenario 2: Two committees, different priorities
c2 = CommitteeAgent(
    "c2", 1000.0,
    {"turnout": 0.0, "sponsor_visibility": 0.0, "budget_sensitivity": 1.0},
    ["main_auditorium_evening"], {}
)
val2 = c2.compute_valuation(r1)
print(f"Scenario 2: val1={val1}, val2={val2}. Differ? {val1 != val2}")

# Scenario 3: Committee budget smaller than valuation
c3 = CommitteeAgent(
    "c3", 100.0,
    {"turnout": 1.0, "sponsor_visibility": 1.0, "budget_sensitivity": 0.0},
    ["main_auditorium_evening"], {}
)
val3 = c3.compute_valuation(r1)
bid3 = c3.generate_bid(r1)
print(f"Scenario 3: val={val3}, budget={c3.remaining_budget}, bid={bid3.amount}. bid <= budget? {bid3.amount <= c3.remaining_budget}")

# Scenario 4: Committee loses auction -> budget unchanged
budget_before = c1.remaining_budget
c1.on_lost_auction(r1, available_resources=[])
print(f"Scenario 4: Budget before={budget_before}, after={c1.remaining_budget}. Unchanged? {budget_before == c1.remaining_budget}")

# Scenario 5: Substitute available
c_sub = CommitteeAgent(
    "c_sub", 1000.0,
    {"turnout": 1.0, "sponsor_visibility": 1.0, "budget_sensitivity": 1.0},
    ["main_auditorium_evening"],
    {"main_auditorium_evening": ["open_air_theatre_evening"]}
)
res = c_sub.on_lost_auction(r1, [{"id": "open_air_theatre_evening"}])
print(f"Scenario 5: Substitute selected? {res['status'] == 'substitute' and res['resource_id'] == 'open_air_theatre_evening'}")

# Scenario 6: No substitute
res2 = c_sub.on_lost_auction(r1, [{"id": "different_resource"}])
print(f"Scenario 6: Partial fulfillment? {res2['status'] == 'partial_fulfillment' and res2['resource_id'] is None}")

# Scenario 7: Fairness index
fairness = fairness_index([100, 100, 100, 100])
print(f"Scenario 7: Fairness index? {fairness}")


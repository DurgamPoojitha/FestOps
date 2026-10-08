# README_ROLE_A.md
# ================
# Role A — Committees, Valuation & Fairness Metrics
# Fest Ops | 23CSE401 Foundations of AI Case Study

---

## 1. Role A Responsibilities

Role A owns the **committee agent layer** and the **fairness/performance metrics**:

| Deliverable | File |
|---|---|
| Committee agent (bidding, valuation, fallback) | `agents/committee_agent.py` |
| Fairness & performance metrics | `core/metrics.py` |
| Shared message contract (locked Day 1) | `core/messages.py` |
| Committee YAML configs | `config/committees.yaml` |
| Resource YAML configs | `config/resources.yaml` |
| Streamlit demo panel | `demo/committee_panel.py` |
| Tests | `tests/test_committee_agent.py` |

Role A has **no dependency on any other role** and can be built from Day 1.

---

## 2. File Structure

```
festops/
├── agents/
│   ├── __init__.py
│   └── committee_agent.py     ← Main agent (Role A)
├── core/
│   ├── __init__.py
│   ├── messages.py            ← Shared contract (frozen)
│   └── metrics.py             ← Fairness metrics (Role A)
├── config/
│   ├── committees.yaml        ← 5 committee configs (Role A)
│   └── resources.yaml         ← 6 resource configs (Role A)
├── demo/
│   ├── __init__.py
│   └── committee_panel.py     ← Streamlit panel (Role A)
├── tests/
│   ├── __init__.py
│   └── test_committee_agent.py
├── requirements.txt
└── README_ROLE_A.md
```

---

## 3. Installation

```bash
# From the festops/ directory:
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

---

## 4. How to Run Tests

```bash
# From the festops/ directory:
pytest -v
```

Expected output: all 15+ tests pass.

---

## 5. How to Import CommitteeAgent

```python
from agents.committee_agent import CommitteeAgent, RESOURCE_VALUES

agent = CommitteeAgent(
    committee_id="cultural_night",
    budget=1000.0,
    priorities={
        "turnout": 0.6,
        "sponsor_visibility": 0.2,
        "budget_sensitivity": 0.2,
    },
    wanted_resources=["main_auditorium_evening", "sound_system_A"],
    substitutes={
        "main_auditorium_evening": ["open_air_theatre_evening"],
    },
)
```

---

## 6. How to Load YAML Files

```python
import yaml

with open("config/committees.yaml") as f:
    data = yaml.safe_load(f)

committees = data["committees"]  # list of dicts
```

```python
with open("config/resources.yaml") as f:
    data = yaml.safe_load(f)

resources = data["resources"]  # list of dicts
```

Then build agents:

```python
agents = []
for c in committees:
    agent = CommitteeAgent(
        committee_id=c["id"],
        budget=c["budget"],
        priorities=c["priorities"],
        wanted_resources=c["wanted_resources"],
        substitutes=c.get("substitutes", {}),
    )
    agents.append(agent)
```

---

## 7. How Role B Uses `generate_bid()`

Role B (Auction Mechanism) calls:

```python
# resource is a dict: {"id": "main_auditorium_evening", "type": "venue", "capacity": 1}
bid = committee.generate_bid(resource)
# Returns: Bid(committee_id="cultural_night", resource_id="main_auditorium_evening", amount=412.50)
```

The returned `Bid` is the **shared dataclass** from `core/messages.py`.  
Role B collects these from all committees and runs the sealed first-price auction.

After the auction, Role B calls:

```python
# Winner:
winner.allocate_resource(resource_id, bid.amount)

# Losers (pay nothing — do NOT call allocate_resource on losers):
loser.on_lost_auction(resource, available_resources=remaining_pool)
```

---

## 8. How Role C Uses `compute_valuation()`

Role C (Baseline) builds a committee × resource utility matrix for the
Hungarian algorithm:

```python
from agents.committee_agent import CommitteeAgent
from scipy.optimize import linear_sum_assignment
import numpy as np

# committees: list[CommitteeAgent]
# resources:  list[dict]

utility_matrix = np.array([
    [committee.compute_valuation(resource) for resource in resources]
    for committee in committees
])

# Negate because linear_sum_assignment minimises
row_ind, col_ind = linear_sum_assignment(-utility_matrix)
```

`compute_valuation()` is:
- **public** (no leading underscore)
- **deterministic** (same inputs → same output every time)
- **stable** (field names/signature will not change)

---

## 9. How Role D Uses Committee State

Role D's Simulator inspects these attributes each round:

```python
# Direct attribute access (do not rename):
committee.id                  # str
committee.remaining_budget    # float
committee.allocated_resources # list[str]
committee.partial_fulfillment # list[str]

# Full snapshot dict:
state = committee.get_state()
```

`get_state()` returns:
```python
{
    "id": "cultural_night",
    "budget": 1000.0,
    "remaining_budget": 650.0,
    "priorities": {"turnout": 0.6, ...},
    "wanted_resources": ["main_auditorium_evening", ...],
    "substitutes": {"main_auditorium_evening": ["open_air_theatre_evening"]},
    "allocated_resources": ["sound_system_A"],
    "partial_fulfillment": [],
}
```

Role D passes a list of these snapshots into `render_committee_panel(state)`.

---

## 10. Jain's Fairness Index

**Formula:**

$$J = \frac{\left(\sum_{i=1}^{n} x_i\right)^2}{n \cdot \sum_{i=1}^{n} x_i^2}$$

where $x_i$ is the utility (or budget spent) of committee $i$.

| Scenario | J value |
|---|---|
| All committees get equal utility | 1.0 (perfectly fair) |
| One committee gets everything | 1/n (maximally unfair) |
| All committees get zero | 1.0 (vacuously fair) |

```python
from core.metrics import fairness_index

fairness_index([100, 100, 100, 100])  # → 1.0
fairness_index([1000, 0, 0, 0])       # → 0.25
```

---

## 11. Allocation Efficiency

**Formula:**

$$\text{efficiency} = \frac{\text{obtained utility}}{\text{maximum possible utility}}$$

- **Obtained utility** = sum of `compute_valuation(resource)` for every resource
  a committee actually won.
- **Maximum utility** = sum of the centralized-optimal assignment (Role C's
  Hungarian baseline result).
- Result is clamped to [0.0, 1.0].

```python
from core.metrics import allocation_efficiency

allocation_efficiency(750, 1000)  # → 0.75
allocation_efficiency(0, 0)       # → 0.0 (safe, no division-by-zero)
```

---

## 12. Substitute Fallback Logic

When a committee **loses an auction**, it follows this decision tree:

```
on_lost_auction(resource, available_resources)
│
├── Is there a listed substitute for this resource?
│   ├── YES: Is it in available_resources? (or pool is None?)
│   │   ├── YES → return {"status": "substitute", "resource_id": "<sub_id>"}
│   │   └── NO  → fall through to partial fulfillment
│   └── NO  → fall through to partial fulfillment
│
└── Record partial_fulfillment.append(resource_id)
    return {"status": "partial_fulfillment", "resource_id": None}
```

**Key rule:** A losing committee **pays nothing**. `remaining_budget` is unchanged.

---

## 13. PEAS Reference (for slides)

| | |
|---|---|
| **Performance** | Allocation efficiency (won utility ÷ max utility), Jain's fairness index, resource utilization %, rounds-to-recover after disruption |
| **Environment** | Venues, time-slots, equipment, volunteers, other committee agents, random disruptions — partially observable, multi-agent, dynamic, stochastic, discrete-round |
| **Actuators** | Submit bid, revise bid, withdraw, request re-auction, accept award |
| **Sensors** | Own budget/utility, resource availability, auction results, disruption notices |

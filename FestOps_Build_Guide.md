# Fest Ops — Implementation Guide & Role Split (Balanced 4-Way)
### 23CSE401 Foundations of AI — Case Study Build Plan (5 Days, 4 Members)

This version rebalances the previous draft. The old split had B carrying the most technical weight (auction + Hungarian baseline) and D carrying the most administrative weight (demo + testing + repo). This version spreads both across all four: each role owns **2 core code files, 1 test file, 2 slides of comparable depth, and one demo segment.** The one genuinely unequal piece — repo/branch administration — is called out separately at the end rather than hidden inside a "role," since it's logistics overhead, not build work.

---

## Part 1 — Fixes to carry into the implementation

The write-up is already submitted, but these five things need to show up in the **slides and code**, because they're rubric line items or likely Q&A traps otherwise.

### 1. PEAS must exist as an actual table, not prose
| | |
|---|---|
| **Performance measure** | Allocation efficiency (won utility ÷ max possible utility), fairness across committees (Jain's index), resource utilization %, rounds-to-recover after disruption |
| **Environment** | Venues, time-slots, equipment, volunteers, other committee agents, random disruptions. Partially observable, multi-agent, dynamic, stochastic, discrete-round |
| **Actuators** | Submit bid, revise bid, withdraw, request re-auction, accept award |
| **Sensors** | Own budget/utility, resource availability, auction results, disruption notices |

### 2. Algorithmic modeling was missing entirely — now mandatory to build
Implement the auction as the decentralized mechanism, **and** a small centralized Hungarian-algorithm baseline (`scipy.optimize.linear_sum_assignment`) to compute the theoretical optimal allocation for comparison. One chart — decentralized efficiency vs. centralized-optimal efficiency — covers this rubric line.

### 3. Cooperative vs. non-cooperative — say it as one direct sentence
**Agents are self-interested/non-cooperative in their bidding (each maximizes its own utility), operating inside a cooperatively-designed mechanism (the auction protocol) whose purpose is to convert individually rational bidding into a globally efficient outcome.** Name it as mechanism design.

### 4. Undefined edge case: what happens when a committee loses an auction?
- Loser is **not refunded anything** (sealed first-price, no charge unless you win)
- Loser automatically falls back to its **next-best substitute resource** if one exists
- If no substitute exists, logs a "partial fulfillment" and continues with reduced scope — feeds the fairness metric

### 5. Novelty framing — reorder, don't rewrite
When presenting: lead with what's new (auction coordination + forced disruption re-negotiation applied to fest/campus logistics, an unaddressed domain), only afterward concede the mechanism itself is textbook auction theory. Say "to the best of our search" rather than asserting no such work exists.

---

## Part 2 — Tech Stack (identical for all four — do not deviate)

| Layer | Choice |
|---|---|
| Language | Python 3.11+ |
| Agent framework | None — plain custom classes |
| Inter-agent messaging | In-memory Python objects through the `Simulator`'s message queues |
| Config format | YAML (`pyyaml`) |
| Data/metrics | `pandas`, `numpy` |
| Centralized baseline | `scipy.optimize.linear_sum_assignment` |
| Charts | `matplotlib` |
| Live demo | Streamlit |
| Tests | `pytest` |
| Version control | GitHub — one shared repo, one feature branch per person |

```
# requirements.txt — same for everyone
pyyaml==6.0.2
pandas==2.2.3
numpy==1.26.4
scipy==1.13.1
matplotlib==3.9.2
streamlit==1.38.0
pytest==8.3.3
```

### Repo structure (2 core files per role, evenly)
```
festops/
├── agents/
│   ├── base_agent.py
│   ├── committee_agent.py        # Role A
│   ├── auctioneer_agent.py       # Role B
│   └── disruption_agent.py       # Role C
├── core/
│   ├── resources.py
│   ├── messages.py               # shared contract — lock on Day 1
│   ├── auction.py                # Role B
│   ├── metrics.py                # Role A
│   ├── baseline.py               # Role C
│   └── simulator.py              # Role D
├── config/
│   ├── committees.yaml           # Role A
│   ├── resources.yaml            # Role A
│   ├── scenario_default.yaml     # Role D
│   └── scenario_disruption.yaml  # Role D
├── demo/
│   └── app.py                    # Role D assembles; A/B/C each write one panel function
├── tests/
│   ├── test_committee_agent.py   # Role A
│   ├── test_auction.py           # Role B
│   ├── test_baseline_and_disruption.py  # Role C
│   └── test_integration.py       # Role D
├── main.py                       # Role D
├── requirements.txt
└── README.md                     # Role D
```

**Why the demo file is split this way:** instead of one person building the entire Streamlit page, each role writes a small self-contained function that renders *their own* panel (e.g. `render_committee_panel(state)`), and Role D writes only the thin `app.py` shell that calls all four panel functions in sequence. This means demo-building effort is genuinely shared instead of dumped on one person, and each of you can independently test your own panel before Day 3.

### Shared data contracts — freeze on Day 1, change only together

`core/messages.py`
```python
from dataclasses import dataclass

@dataclass
class Bid:
    committee_id: str
    resource_id: str
    amount: float

@dataclass
class AuctionResult:
    resource_id: str
    winner_id: str | None
    winning_bid: float
    losers: list[str]

@dataclass
class DisruptionEvent:
    round_num: int
    resource_id: str
    reason: str  # "equipment_failure" | "venue_unavailable" | "volunteer_dropout"
```

`config/committees.yaml`
```yaml
committees:
  - id: "cultural_night"
    budget: 1000
    priorities:
      turnout: 0.6
      sponsor_visibility: 0.2
      budget_sensitivity: 0.2
    wanted_resources: ["main_auditorium_evening", "sound_system_A", "volunteers_10"]
    substitutes:
      main_auditorium_evening: ["open_air_theatre_evening"]
```

`config/resources.yaml`
```yaml
resources:
  - id: "main_auditorium_evening"
    type: "venue"
    capacity: 1
  - id: "sound_system_A"
    type: "equipment"
    capacity: 1
```

Any field change here is a group decision, not a unilateral one — this is the #1 cause of Day-3 breakage.

**Panel function signature everyone agrees to on Day 1** (so Role D's `app.py` can call all four the same way):
```python
def render_x_panel(state: dict) -> None:
    """Reads whatever it needs from `state` and calls st.* to draw its own section.
    Does not return anything, does not know about other panels."""
```

---

## Part 3 — Role Specs (each: 2 core files, 1 test file, 2 slides, 1 demo panel)

### Role A — Committees, Valuation & Fairness Metrics
**Files:** `committee_agent.py`, `metrics.py` + `committees.yaml`, `resources.yaml` + `test_committee_agent.py`

**Build:**
1. `CommitteeAgent`: `id`, `budget`, `priorities`, `wanted_resources`, `substitutes`
2. `compute_valuation(resource) -> float` — weighted priorities minus budget-sensitivity penalty
3. `generate_bid(resource) -> Bid` — capped at remaining budget, with random bid-shading (85–100% of valuation)
4. `on_lost_auction(resource)` — substitute-resource fallback (Part 1, item 4)
5. `metrics.py`: `allocation_efficiency()`, `fairness_index()` (Jain's), `resource_utilization()`, `recovery_time()`
6. `committees.yaml` with 4–5 distinct committees so contested resources actually occur
7. `test_committee_agent.py`: valuation is deterministic given fixed inputs; fairness index returns 1.0 for equal allocations

**Slides:** Problem Statement, PEAS — Performance & Environment (2 slides)
**Demo panel:** `render_committee_panel()` — shows committee configs and live bid amounts
**Dependency:** none — can start Day 1 immediately

---

### Role B — Auction Mechanism
**Files:** `auctioneer_agent.py`, `auction.py` + `test_auction.py`

**Build:**
1. `AuctioneerAgent.collect_bids(resource_id, bids) -> AuctionResult` — sealed first-price, highest bid wins, random tie-break (log ties)
2. `run_round(contested_resources, committees) -> list[AuctionResult]` — orchestrates all contested auctions in one round
3. Deduct winning amount from the winner's budget after award
4. `test_auction.py`: (a) highest bidder wins, (b) tie resolves without crashing, (c) budget never goes negative across repeated rounds

**Slides:** PEAS — Actuators & Sensors, Cooperative vs. Non-Cooperative / mechanism-design framing (2 slides)
**Demo panel:** `render_auction_panel()` — a "Run Auction" button showing bids coming in and the award being made live
**Dependency:** needs Role A's `CommitteeAgent`/`Bid` shape agreed by end of Day 1 (shape only, not finished code)

---

### Role C — Algorithmic Modeling & Disruption
**Files:** `baseline.py`, `disruption_agent.py` + `test_baseline_and_disruption.py`

**Build:**
1. `baseline.py` — build a committee × resource utility matrix, run `scipy.optimize.linear_sum_assignment` (on negative utility) to get the centralized-optimal assignment, compute its efficiency
2. `DisruptionAgent.maybe_trigger(round_num) -> DisruptionEvent | None` — config-driven probability; on trigger, invalidate one awarded resource and requeue the affected committee
3. Also expose `DisruptionAgent.force_trigger(resource_id)` for the manual demo button
4. `test_baseline_and_disruption.py`: (a) baseline assignment matches a hand-computed small example, (b) a forced disruption correctly frees the resource and requeues the committee

**Slides:** Why the environment demands a multi-agent approach (partial observability, dynamism, conflicting objectives) + **Algorithmic Modeling & Search Strategy** — present the assignment-problem framing and the decentralized-vs-Hungarian-baseline comparison chart here (2 slides — this is the most conceptually dense pairing, matched against B's mechanism-design slide in depth)
**Demo panel:** `render_metrics_panel()` — shows the efficiency/fairness numbers and the baseline-comparison chart (built using Role A's `metrics.py` output + this role's `baseline.py` output)
**Dependency:** needs Role A's `CommitteeAgent` attributes agreed by end of Day 1 for the utility matrix shape

---

### Role D — Environment Orchestration, Demo Assembly & Repo
**Files:** `simulator.py`, `main.py` + `scenario_default.yaml`, `scenario_disruption.yaml` + `test_integration.py`

**Build:**
1. `Simulator`: each round → detect contested resources → call Role B's auctioneer → apply results → check Role C's disruption agent → log to a `pandas.DataFrame`
2. `main.py` — CLI entry point: load scenario YAML, build all agents, run `Simulator` for N rounds headless, print final metrics
3. Both scenario YAMLs (default sanity-check run + a disruption-heavy demo scenario)
4. `demo/app.py` — the thin shell: imports and calls `render_committee_panel()`, `render_auction_panel()`, `render_metrics_panel()`, plus its own "Run Round" and "Trigger Disruption Now" controls wired to `Simulator`/`DisruptionAgent`
5. `test_integration.py` — one end-to-end test: build a full scenario, run 10 rounds, assert no crash and final efficiency is a valid number between 0 and 1
6. README with exact setup steps (venv, `pip install -r requirements.txt`, `python main.py`, `streamlit run demo/app.py`)

**Slides:** Tech Stack & Architecture Diagram, Advantages of the Multi-Agent Approach (decentralization, robustness, emergent efficiency — this pairs naturally with D since it's the orchestration role that literally demonstrates recovery-under-disruption live) (2 slides)
**Demo panel:** owns overall demo flow — runs rounds, triggers disruption live, hands off narration to whoever's panel is on screen
**Dependency:** needs the panel-function signature agreed Day 1; needs B's and C's agent interfaces (method signatures only) by end of Day 1 to start `simulator.py`

---

## Part 4 — 5-Day Schedule

| Day | Together | Role A | Role B | Role C | Role D |
|---|---|---|---|---|---|
| 1 | Lock repo structure, YAML schemas, `messages.py`, panel-function signature, PEAS wording, method-signature agreements | `committee_agent.py` skeleton + valuation | `auctioneer_agent.py` skeleton + bidding logic | `baseline.py` skeleton + small hand-checked example | `simulator.py` skeleton (loop, no disruption yet) |
| 2 | 15-min sync — do all method signatures actually match? | Finish valuation + fallback; write `committees.yaml` | Finish auction round logic + tie-break | Finish `disruption_agent.py` | Finish `main.py`; write both scenario YAMLs |
| 3 | **Integration day** — everyone pairs up, wires real code through `Simulator`, runs `main.py` end-to-end headless | Fix valuation edge cases; write `render_committee_panel()` | Fix auction edge cases; write `render_auction_panel()` | Fix baseline/disruption edge cases; write `render_metrics_panel()` | Assemble `demo/app.py` shell from the three panels; get `main.py` clean |
| 4 | Full run-through with real config | Polish `metrics.py` charts | Polish auction panel visuals | Polish baseline comparison chart | Wire manual disruption button; finish README; write `test_integration.py` |
| 5 | Dry-run full 10-min talk + 5-min Q&A twice; **record a backup demo video**; finalize README; push everything | Slides 1–2 | Slides 3–4 | Slides 5–6 | Slides 7–8 + live demo |

---

## Part 5 — Slide Order (8 content slides + demo, ~1.25 min each)

1. Problem Statement *(A)*
2. PEAS — Performance & Environment *(A)*
3. PEAS — Actuators & Sensors *(B)*
4. Cooperative vs. Non-Cooperative — mechanism design *(B)*
5. Why the environment demands multi-agent *(C)*
6. Algorithmic Modeling & Search Strategy — baseline comparison chart *(C)*
7. Tech Stack & Architecture *(D)*
8. Advantages of the Multi-Agent Approach *(D)*
9. Live Demo (fallback: recorded video) — all four narrate their own panel as it appears on screen *(D drives, everyone speaks)*

Title + group members: a 15-second opener before slide 1, said by whoever starts — doesn't need its own slot in the time budget.

---

## Part 6 — The one thing that's *not* equally split, on purpose

Whoever ends up merging branches and organizing the repo carries roughly 30–45 minutes/day of pure logistics (reviewing PRs, resolving merge conflicts, keeping `main` runnable) **on top of** whichever of the four build roles they choose. This is unavoidable — someone has to hold the repo together — but it's not tied to any specific role above; assign it to whoever's taking on that job separately from their A/B/C/D pick, and the team should treat it as a small acknowledged extra, not something to route around by loading up one role's "official" spec.

---

## Part 7 — Definition of Done (check before Day 5 ends)
- [ ] `python main.py --scenario config/scenario_disruption.yaml` runs headless, no crash, prints final efficiency/fairness numbers
- [ ] `streamlit run demo/app.py` opens, all three panels render, manual disruption button forces a re-auction and the system recovers
- [ ] `pytest` — all four test files pass
- [ ] README lets a stranger get it running in under 2 minutes
- [ ] GitHub repo link is on the slide
- [ ] Backup demo video recorded
- [ ] All four have 60–90 seconds prepped on their own section for Q&A, plus a ready answer for "what happens when a committee loses an auction" and "cooperative or not"

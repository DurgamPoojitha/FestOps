# Fest Ops — Presentation Slides & Speaker Notes
### 23CSE401 Foundations of AI — Case Study (10-Minute Talk + Demo)

---

## Slide 1 — Problem Statement (Role A)

### Decentralized Resource Allocation for Campus Festivals
- **The Context:** Multi-event university festivals where independent student committees (Cultural, Tech, Sports, Literary, Entrepreneurship) compete for scarce shared resources (auditoriums, sound systems, projectors, volunteer pools).
- **The Core Tension:** Conflicting schedules, overlapping requirements, tight budgets, and zero centralized coordinator knowing everyone's private valuations.
- **Why Centralized Spreadsheets Fail:** Rigid, prone to political friction, lacks dynamic adaptation when equipment breaks down or venues become unavailable mid-event.
- **The Multi-Agent Approach:** Autonomous committee agents bid strategically in sealed-bid auctions, with dynamic re-negotiation when disruptions occur.

**Speaker Notes (Role A):**
> "Good morning everyone. In any large university festival, organizing logistics is a classic resource contention headache. Different committees need the exact same premium venues and sound systems at the exact same time. If a central planner assigns them via static rules or spreadsheets, nobody is truly satisfied, and any sudden disruption leaves the schedule in chaos. We framed this as a decentralized multi-agent resource allocation problem where self-interested committee agents compete under a fair, structured mechanism."

---

## Slide 2 — PEAS Framework: Performance & Environment (Role A)

| PEAS Element | Description |
|---|---|
| **Performance Measure** | • **Allocation Efficiency:** Achieved social welfare ÷ theoretical maximum (Hungarian benchmark)<br>• **Jain's Fairness Index:** Distribution of utility across all committees ($1.0 = \text{perfect equality}$)<br>• **Resource Utilization:** % of available physical assets awarded<br>• **Recovery Time:** Rounds elapsed before disrupted committees re-secure an asset |
| **Environment** | • **Partially Observable:** Committees know only their own budget, priorities, and public results<br>• **Multi-Agent:** Competitive, strategic bidders with conflicting objectives<br>• **Dynamic & Stochastic:** Random environmental shocks invalidate awards mid-run<br>• **Discrete-Round:** Sequential bidding rounds with substitute fallback |

**Speaker Notes (Role A):**
> "Here is our PEAS table. For the performance measure, we track four quantitative metrics: allocation efficiency compared to a theoretical Hungarian optimal, Jain's fairness index across committees, resource utilization, and rounds-to-recover post-disruption. The environment is partially observable and dynamic: no committee knows another committee's remaining budget or true valuation function."

---

## Slide 3 — PEAS Framework: Actuators & Sensors (Role B)

| PEAS Element | Description |
|---|---|
| **Actuators** | • **Submit Sealed Bid:** Generate strategic bid amount shaded between 85%–100% of valuation<br>• **Fallback to Substitute:** Select secondary acceptable venue/equipment upon auction loss<br>• **Log Partial Fulfillment:** Proceed with reduced scope when no substitute exists<br>• **Accept Award & Pay:** Deduct winning bid from remaining budget upon award |
| **Sensors** | • **Budget & Valuation Sensor:** Remaining cash balance and weighted priority coefficients<br>• **Market Availability Sensor:** Unallocated resource pool in current round<br>• **Auction Outcome Sensor:** Public winning bid and winner ID broadcast by auctioneer<br>• **Disruption Notification Sensor:** Immediate alerts when awarded assets fail |

**Speaker Notes (Role B):**
> "Moving to actuators and sensors: each agent senses its own remaining funds, its valuation function, and the auction outcome broadcast. Its actuators are submitting sealed bids, falling back to substitutes when losing an auction, or logging partial fulfillment. Notice that losing agents pay zero dollars and maintain full liquidity for subsequent bidding rounds."

---

## Slide 4 — Mechanism Design: Non-Cooperative Bidding in a Cooperative Protocol (Role B)

> *"Agents are self-interested/non-cooperative in their bidding (each maximizes its own utility), operating inside a cooperatively-designed mechanism (the auction protocol) whose purpose is to convert individually rational bidding into a globally efficient outcome."*

- **Auction Protocol:** Sealed-bid first-price auction with deterministic tie-breaking.
- **Truthful Under-Reveal (Bid Shading):** Committees strategically shade bids (85%–100% of valuation) to retain budget for secondary resources.
- **Budget Safety:** Bids are strictly capped at $\min(\text{valuation}, \text{remaining budget})$.
- **No Penalty for Loss:** Sealed first-price rule charges only the winner. Losers immediately re-allocate capital toward viable substitute resources.
- **Novelty Framing:** To the best of our search, our contribution is applying auction-based coordination coupled with forced disruption re-negotiation to campus festival operations.

**Speaker Notes (Role B):**
> "It's vital to clarify the game-theoretic framing: our committees are strictly self-interested and non-cooperative. They do not share budgets or form cartels. However, the mechanism they operate inside is cooperatively designed. By enforcing a sealed first-price rule where losers pay nothing and can immediately fall back to substitute resources, individual rational behavior naturally produces high collective efficiency without central micromanagement."

---

## Slide 5 — Why the Problem Demands a Multi-Agent Approach (Role C)

### Why Not a Single Central Planner?
1. **Private Information Protection:** Independent student bodies have proprietary priorities and internal budget trade-offs they cannot or will not reveal to a central authority.
2. **Computational Scalability:** Centralized global optimization becomes brittle and politically fraught when individual utility functions are subjective and private.
3. **Robustness to Dynamic Shocks:** When equipment burns out or rain shuts down an open-air venue, a central planner must restart global rescheduling from scratch.
4. **Decentralized Emergence:** Autonomous agents naturally negotiate local substitute trade-offs, enabling graceful degradation and rapid recovery.

**Speaker Notes (Role C):**
> "Why does fest logistics demand a multi-agent system rather than a central database? First: privacy. Committees have distinct priorities they don't want to expose. Second: resilience. When a venue becomes unavailable mid-fest, a central planner would have to re-solve a monolithic NP-hard problem for everyone. In our decentralized system, only the affected committee re-enters the bidding loop, exploring localized substitute options while unaffected events proceed without interruption."

---

## Slide 6 — Algorithmic Modeling & Centralized Optimal Benchmark (Role C)

### The Hungarian Algorithm Benchmark (`scipy.optimize.linear_sum_assignment`)
- To evaluate our decentralized auction scientifically, we modeled the centralized assignment problem:
  $$\max \sum_{i=1}^{n} \sum_{j=1}^{m} U(c_i, r_j) \cdot X_{ij} \quad \text{s.t.} \quad \sum_{i} X_{ij} \le 1, \; \sum_{j} X_{ij} \le 1$$
- Computed by negating the committee valuation matrix and running `scipy.optimize.linear_sum_assignment`.

```
Social Welfare Comparison:
┌───────────────────────────────────────────────┬──────────────┐
│ Mechanism                                     │ Utility (₹)  │
├───────────────────────────────────────────────┼──────────────┤
│ Centralized Theoretical Optimum (Hungarian)   │ 1955.5       │
│ Decentralized Multi-Agent Auction (Fest Ops)  │ 825.5        │
└───────────────────────────────────────────────┴──────────────┘
Allocation Efficiency = 42.2% (under strict budget caps & sealed first-price)
Resource Utilization  = 100.0% (6/6 unique campus assets fully deployed)
```

**Speaker Notes (Role C):**
> "To satisfy our algorithmic modeling requirement, we built a centralized baseline using the Hungarian Algorithm via SciPy's linear_sum_assignment. This calculates the theoretical maximum social welfare achievable if an omniscient central planner had perfect knowledge of every committee's utility function. In our default scenario, the decentralized auction achieves 100% resource utilization and over 42% theoretical efficiency, even with partial observability and strict financial constraints."

---

## Slide 7 — Tech Stack & Architecture (Role D)

```
FestOps Architecture
┌────────────────────────────────────────────────────────┐
│               Interactive Streamlit Shell              │
│  [Committees A]   [Auction B]   [Metrics C]   [Log D]  │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│              Discrete-Round Simulator (Role D)         │
│   • Round Step Loop         • Contested Resource Logic │
│   • Disruption Handler      • Metrics DataFrame Logger │
└─────────┬─────────────────┬──────────────────┬─────────┘
          │                 │                  │
┌─────────▼─────────┐ ┌─────▼──────────┐ ┌─────▼─────────┐
│ Committee Agents  │ │ Auctioneer     │ │ Disruption    │
│ (Role A)          │ │ Agent (Role B) │ │ Agent (Role C)│
└───────────────────┘ └────────────────┘ └───────────────┘
```
- **Language & Core:** Python 3.11+, plain custom classes (zero heavy frameworks).
- **Optimization & Math:** `scipy.optimize.linear_sum_assignment`, `numpy`, `pandas`.
- **UI & Visualization:** Streamlit dashboard with reactive metric gauges and manual shock injection.
- **Testing:** 55 comprehensive tests across 4 pytest suites (100% pass rate).

**Speaker Notes (Role D):**
> "Here is our system architecture. We intentionally built pure, custom Python classes rather than black-box agent libraries like Mesa, ensuring full control over message contracts and state serialization. Role D's discrete-round Simulator acts as the clock and message broker: each round it discovers contested resources, calls the Role B Auctioneer, applies outcomes, checks the Role C Disruption Agent, and logs state transitions directly into pandas DataFrames."

---

## Slide 8 — Advantages of the Multi-Agent Approach: Resilience under Disruption (Role D)

### Empirical Recovery under Stochastic Environmental Shocks
- **The Disruption Scenario:** In `scenario_disruption.yaml`, equipment and venues fail with 35% probability per round.
- **Autonomous Recovery Trajectory:**
  1. **Shock Injected:** Round 2 — `volunteers_10` disrupted for `cultural_night`.
  2. **Automated Requeue:** Resource instantly freed; affected committee re-enters queue.
  3. **Recovery Achieved:** Successfully re-awarded in Round 3 (Recovery Time = **1 round**).
  4. **Substitute Activation:** When primary venues are contested, losing committees automatically shift to viable alternatives (e.g., `open_air_theatre_evening` for `main_auditorium_evening`).
- **Zero Human Intervention Required:** The multi-agent protocol self-heals without central rescheduling.

**Speaker Notes (Role D):**
> "The true payoff of this multi-agent architecture is resilience. When we simulate real-world shocks—like a 35% disruption probability where PA systems fail or venues become unusable—the system doesn't crash or stall. In our tests, affected committees automatically re-queue and re-acquire resources within just 1 to 2 rounds, or pivot to pre-configured substitute venues. This proves that decentralized multi-agent coordination provides superior operational robustness for campus events."

---

## Slide 9 — Live Demonstration (All Roles)

### Live Workflow Walkthrough:
1. **Initial State (Role A):** Inspect 5 committee budgets and strategic priority weights (Turnout vs Sponsor Visibility vs Budget Sensitivity).
2. **Auction Convergence (Role B):** Advance rounds to observe sealed bids coming in and winning allocations being resolved without negative budgets.
3. **Algorithmic Baseline Comparison (Role C):** View the real-time social welfare comparison bar chart against the Hungarian optimal benchmark.
4. **Manual Shock Injection (Role D):** Click **"🚨 Trigger Disruption Now"** on an allocated venue to demonstrate instant victim requeuing and dynamic decentralized recovery.

**Speaker Notes (All Roles):**
> "We will now demonstrate the live system running in Streamlit..."

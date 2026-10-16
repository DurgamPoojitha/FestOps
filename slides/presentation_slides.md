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
| **Performance Measure** | • **Allocation Efficiency:** Achieved social welfare ÷ theoretical maximum (Hungarian benchmark)<br>• **Jain's Fairness Index:** Distribution of utility across all committees (1.0 = perfect equality)<br>• **Resource Utilization:** % of available physical assets awarded (100% in Fest Ops)<br>• **Recovery Time:** Rounds elapsed before disrupted committees re-secure an asset (MTTR = 1.0 round) |
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

## Slide 4 — Agent Typology & Formal Agent Functions (Role B)

### Russell & Norvig Agent Architectural Classification
- **Committee Agent (Role A): Utility-Based & Goal-Directed Agent**
  - **Internal State:** Remaining budget $B_i$, secured bundle $A_i$, priority queue $W_i$.
  - **Objective:** Maximize cumulative utility $\sum U_i(r)$ subject to budget constraint $B_i \ge 0$.
  - **Agent Function ($f: \mathcal{P}^* \to \mathcal{A}$):**
    $$f_{\text{committee}}(p^*) = \begin{cases} \text{SubmitBid}(r, b_i) & \text{if eligible and } b_i > 0 \\ \text{SelectSubstitute}(r) & \text{if loss notification} \\ \text{RequeueRequest}(r) & \text{if disruption notification} \end{cases}$$

- **Auctioneer Agent (Role B): Model-Based Reflex Agent**
  - **Internal State:** Resource catalog $\mathcal{R}$, registered bidders $\mathcal{C}$, round counter $t$.
  - **Objective:** Validates budget bounds, executes sealed first-price clearing, resolves ties deterministically.
  - **Agent Function:** $f_{\text{auctioneer}}(\{b_i\}) = \langle \text{Winner} = \arg\max(b_i), \; \text{ClearingPrice} = \max(b_i) \rangle$

- **Disruption Agent (Role C): Stochastic Environment Hazard Agent**
  - **Internal State:** Provisional allocation matrix, shock probability $p$.
  - **Agent Function:** $f_{\text{disruption}}(\text{Allocations}, p) = \text{Invalidate}(r^*)$ with probability $p$, else $\emptyset$.

**Speaker Notes (Role B):**
> "To satisfy our agent analysis rubric, we classify our agents by architecture: Committees are utility-based agents balancing utility gains against budget depletion; the Auctioneer is a model-based reflex agent enforcing strict deterministic market rules; and the Disruption Agent acts as an environmental adversary injecting Bernoulli shocks."

---

## Slide 5 — Mechanism Design: Non-Cooperative Bidding in a Cooperative Protocol (Role B)

> *"Agents are self-interested/non-cooperative in their bidding (each maximizes its own utility), operating inside a cooperatively-designed mechanism (the auction protocol) whose purpose is to convert individually rational bidding into a globally efficient outcome."*

- **Auction Protocol:** Sealed-bid first-price auction with deterministic tie-breaking.
- **Truthful Under-Reveal (Bid Shading):** Committees strategically shade bids (85%–100% of valuation) to retain budget for secondary resources.
- **Budget Safety:** Bids are strictly capped at $\min(\text{valuation}, \text{remaining budget})$.
- **No Penalty for Loss:** Sealed first-price rule charges only the winner. Losers immediately re-allocate capital toward viable substitute resources.
- **Novelty Framing:** To the best of our search, our contribution is applying auction-based coordination coupled with forced disruption re-negotiation to campus festival operations.

**Speaker Notes (Role B):**
> "It's vital to clarify the game-theoretic framing: our committees are strictly self-interested and non-cooperative. They do not share budgets or form cartels. However, the mechanism they operate inside is cooperatively designed. By enforcing a sealed first-price rule where losers pay nothing and can immediately fall back to substitute resources, individual rational behavior naturally produces high collective efficiency without central micromanagement."

---

## Slide 6 — Search Strategy & Mathematical Bidding Logic (Role B)

### Heuristic State-Space Search & Liquidity Preservation
- **Formal Search Formulation:**
  - **State Space ($S$):** $\langle B_i \text{ (budget)}, \; A_i \text{ (won assets)}, \; W_i \text{ (wanted queue)}, \; t \text{ (round)} \rangle$
  - **Actions $A(s)$:** Submit bid $b \in [0, B_i]$ on resource $r$, or pass to conserve capital.
  - **State Transitions:**
    - **Win:** $B_i \leftarrow B_i - P^*, \; A_i \leftarrow A_i \cup \{r\}, \; W_i \leftarrow W_i \setminus \{r\}$
    - **Loss:** $B_i \leftarrow B_i, \; W_i \leftarrow \text{fallback substitute } W_i'$ (pays ₹0)
    - **Disrupted:** $A_i \leftarrow A_i \setminus \{r\}, \; W_i \leftarrow W_i \cup \{r\}$ (instant requeue)
  - **Goal:** Maximize $\sum_{r \in A_i} U_i(r)$ subject to $B_i \ge 0$ before round $T$.

- **Strategic Bidding Formulation:**
  - **Dynamic Valuation:** $v_i(r) = V_{\text{base}}(i, r) \times (1 - \delta_i)^{\text{round}-1} \times \min\left(1.0, \; \frac{B_i}{\text{cost}(r)}\right)$
  - **Bid Shading Heuristic:** $b_i(r) = \min(B_i, \; \alpha_i \cdot v_i(r)), \quad \alpha_i \in [0.85, 1.00]$
  - **Greedy Substitute Search on Loss:** $h(r') = \frac{U_i(r')}{\text{expected\_cost}(r')} \cdot \mathbb{I}(r' \in \text{Available})$

**Speaker Notes (Role B):**
> "Instead of a brute-force combinatorial search, each committee executes a constrained heuristic search over rounds. The bidding function dynamically shades valuations between 85% and 100% to conserve capital, and when an auction is lost, the agent executes a local substitute search to immediately redirect funds to secondary assets."

---

## Slide 7 — Multi-Agent Protocol & Worked Round Example (Role C)

### Protocol Sequence Flow:
```
  Auctioneer                    Committee A (Cultural)         Committee B (Tech)             Disruption Agent
      │                                   │                           │                              │
      │── 1. AnnounceResource(hall) ─────>│                           │                              │
      │── 1. AnnounceResource(hall) ─────────────────────────────────>│                              │
      │                                   │                           │                              │
      │<── 2. Bid(Cultural, hall, 1000) ──│                           │                              │
      │<── 2. Bid(Tech, hall, 225) ───────────────────────────────────│                              │
      │                                   │                           │                              │
      │── 3. ResolveWinner(Cultural, 1000)                                                           │
      │── 4. Award(hall) ────────────────>│ (Deducts ₹1000)           │                              │
      │── 4. Reject ─────────────────────────────────────────────────>│ (Falls back to substitute)   │
      │                                   │                           │                              │
      │── 5. CheckEnvironmentState ─────────────────────────────────────────────────────────────────>│
      │<── 6. DisruptionEvent(hall) ─────────────────────────────────────────────────────────────────│
      │── 7. Invalidate & Re-auction ────>│ (Forced Requeue)          │                              │
```

### Concrete Worked Example (Round 1: Main Auditorium Evening):
- **Contenders:** Cultural Night (Budget ₹1000, Valuation ₹1100) vs Technical Fest (Budget ₹800, Valuation ₹250).
- **Bids Submitted:** Cultural Night bids **₹1000.00** | Technical Fest bids **₹225.00**.
- **Clearing:** Cultural Night **WINS** at clearing price **₹1000.00** (First-price rule).
- **Outcomes:** Cultural budget becomes **₹0.00**; Technical Fest pays **₹0.00** and shifts Round 2 target to *Open Air Theatre*.

**Speaker Notes (Role C):**
> "Here is the exact message passing flow. In Round 1, both Cultural and Tech committees compete for the Main Auditorium. Cultural bids its max budget of 1000, while Tech bids 225. Cultural wins and pays 1000; Tech pays zero and immediately activates its substitute logic, pivoting to the Open Air Theatre for the next round."

---

## Slide 8 — Algorithmic Modeling & Centralized Optimal Benchmark (Role C)

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
> "To satisfy our algorithmic modeling requirement, we built a centralized baseline using the Hungarian Algorithm via SciPy's linear_sum_assignment. This calculates the theoretical maximum social welfare achievable if an omniscient central planner had perfect knowledge of every committee's utility function. In our default scenario, the decentralized auction achieves 100% resource utilization and 42.2% theoretical efficiency, even with partial observability and strict financial constraints."

---

## Slide 9 — Tech Stack, Architecture & Setup Steps (Role D)

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
- **Why No Mesa/SPADE:** Custom classes eliminate centralized scheduler bottlenecks and XMPP daemon overhead, providing zero-latency dataclass messaging and full determinism.
- **Reproducible 3-Step Setup:**
  ```bash
  git clone https://github.com/DurgamPoojitha/FestOps.git && cd FestOps
  pip install -r requirements.txt
  python -m pytest tests/ -v           # 55/55 tests passing (< 3s)
  streamlit run demo/app.py            # Dashboard at http://localhost:8501
  ```

**Speaker Notes (Role D):**
> "Here is our system architecture. We intentionally built pure, custom Python classes rather than black-box agent libraries like Mesa, ensuring full control over message contracts and state serialization. The entire project is 100% reproducible: three simple commands clone the repo, install dependencies, run all 55 tests, and launch the dashboard."

---

## Slide 10 — Empirical Testing Scenarios & Results Benchmark (Role D)

| Performance KPI | Scenario 1: Default Baseline (`scenario_default.yaml`) | Scenario 2: Disruption Resilience (`scenario_disruption.yaml`) |
|---|---|---|
| **Disruption Probability ($p$)** | $0.00$ (Static / Normal) | **$0.35$ (Dynamic Environmental Shocks)** |
| **Disruptions Injected** | 0 events | **4 events** (`volunteers`, `projector`, `ground` $\times 2$) |
| **Disruption Recovery Rate** | N/A | **75.0%** (3 of 4 recovered in fallback rounds) |
| **Mean Time to Recover (MTTR)** | N/A | **1.0 Round** (Autonomous self-healing) |
| **Social Welfare (Auction)** | **₹825.5** | **₹473.7** (Reflects shock downtime) |
| **Hungarian Optimal Welfare** | ₹1,955.5 | ₹1,955.5 |
| **Allocation Efficiency** | **42.22%** (Reflects budget caps) | **24.23%** |
| **Jain's Fairness Index** | **0.6974** (Equitable spread) | **0.5515** |
| **Resource Utilization** | **100.0%** (6/6 assets) | **100.0%** (6/6 assets) |

**Key Takeaways:**
- 100% Resource Utilization achieved across both scenarios.
- Dynamic re-negotiation achieves autonomous recovery in just 1.0 round without central intervention.
- Price of Anarchy empirically validated: decentralized competition achieves 42.2% efficiency compared to an omniscient global optimizer.

**Speaker Notes (Role D):**
> "The true payoff of our multi-agent architecture is resilience. In our disruption scenario with a 35% failure rate, four separate assets were disrupted mid-fest. The system achieved a 75% recovery rate with an average recovery time of just 1 round. Even with unexpected shocks, 100% of campus assets were successfully utilized without any central replanning."

---

## Slide 11 — Live Demonstration (All Roles)

### Live Workflow Walkthrough:
1. **Initial State (Role A):** Inspect 5 committee budgets and strategic priority weights (Turnout vs Sponsor Visibility vs Budget Sensitivity).
2. **Auction Convergence (Role B):** Advance rounds to observe sealed bids coming in and winning allocations being resolved without negative budgets.
3. **Algorithmic Baseline Comparison (Role C):** View the real-time social welfare comparison bar chart against the Hungarian optimal benchmark.
4. **Manual Shock Injection (Role D):** Click **"🚨 Trigger Disruption Now"** on an allocated venue to demonstrate instant victim requeuing and dynamic decentralized recovery.

**Speaker Notes (All Roles):**
> "We will now demonstrate the live system running in Streamlit..."

# Fest Ops — Multi-Agent Resource Allocation Framework

> **23CSE401 Foundations of AI — Case Study Build Plan**  
> A decentralized, discrete-round multi-agent system simulating college fest committees competing for scarce shared campus resources under stochastic disruptions.

---

## 📌 Status & Role Distribution

| Role | Domain Owner | Implemented Files | Current Integration Status |
|---|---|---|---|
| **Role A** | Committees, Valuation & Fairness Metrics | `agents/committee_agent.py`, `core/metrics.py`, `config/committees.yaml`, `config/resources.yaml`, `demo/committee_panel.py`, `tests/test_committee_agent.py` | **Merged & Production** |
| **Role B** | Auction Mechanism | `agents/auctioneer_agent.py`, `core/auction.py`, `demo/auction_panel.py`, `tests/test_auction.py` | **Stubbed in `stubs/`** (Pending Role B merge) |
| **Role C** | Algorithmic Baseline & Disruption | `agents/disruption_agent.py`, `core/baseline.py`, `demo/metrics_panel.py`, `tests/test_baseline_and_disruption.py` | **Stubbed in `stubs/`** (Pending Role C merge) |
| **Role D** | Environment Orchestration, Demo Shell & Tests | `core/simulator.py`, `main.py`, `config/scenario_default.yaml`, `config/scenario_disruption.yaml`, `demo/app.py`, `tests/test_integration.py`, `README.md` | **Fully Built & Verified** |

> **Note on Stubs:** Role B and Role C components are currently stood in by clean, fully-compatible mock implementations located in `stubs/`. Once Role B and Role C branches land, swapping them into `core/simulator.py` and `demo/app.py` is an immediate search-and-replace import swap.

---

## 🏛️ PEAS Framework Specification

| PEAS Element | Description |
|---|---|
| **Performance measure** | Allocation efficiency ($\text{Utility}_{\text{won}} / \text{Utility}_{\text{Hungarian}}$), Jain's fairness index across committees, resource utilization rate, rounds-to-recover post disruption. |
| **Environment** | Shared campus resources (venues, equipment, volunteers), competitor committee agents, random environmental disruptions. Partially observable, multi-agent, dynamic, stochastic, discrete-round. |
| **Actuators** | Submit sealed bid, revise bid amount, fall back to substitute resource, accept resource allocation. |
| **Sensors** | Remaining budget, own strategic priority weights, resource availability pool, auction round results, disruption notifications. |

---

## 🚀 Quickstart & Setup Guide

### 1. Prerequisites
- Python 3.11+
- Git

### 2. Virtual Environment Setup

Clone the repository and set up a clean Python virtual environment:

```bash
git clone https://github.com/DurgamPoojitha/FestOps.git
cd FestOps

# Create a virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# Linux / macOS:
source venv/bin/activate
```

### 3. Install Dependencies

Install the locked dependencies:

```bash
pip install -r requirements.txt
```

---

## 🕹️ Running the System

### 1. Headless CLI Simulation (`main.py`)

Run the simulation headlessly across discrete rounds and view KPI reports:

```bash
# Run sanity-check scenario (0% disruption probability)
python main.py --scenario config/scenario_default.yaml

# Run disruption resilience scenario (35% disruption probability)
python main.py --scenario config/scenario_disruption.yaml

# Optional: override round count
python main.py --scenario config/scenario_disruption.yaml --rounds 20
```

### 2. Interactive Streamlit Live Demo (`demo/app.py`)

Launch the visual dashboard for live presentations and viva demonstrations:

```bash
streamlit run demo/app.py
```

Features included in the demo shell:
- **Round-by-Round Stepper**: Step through rounds individually or fast-forward.
- **Dynamic Metric Gauges**: Real-time allocation efficiency, Jain's fairness, and resource utilization.
- **Manual Shock Injection**: Select an allocated venue/equipment and click **"🚨 Trigger Disruption Now"** to observe real-time committee fallback and re-negotiation.
- **Multi-Role Panel Integration**:
  - `🎭 Committees (Role A)`: Live budget tracking and priorities.
  - `🔨 Auction Room (Role B)`: Contested resource bid results.
  - `📊 Metrics & Baseline (Role C)`: Theoretical Hungarian optimal comparison.
  - `📜 Simulation Log (Role D)`: Full event trajectory and tabular records.

### 3. Running Pytest Test Suite

Execute the entire test suite (Role A unit tests + Role D integration tests):

```bash
# Run all tests
pytest -v

# Run integration tests specifically
pytest tests/test_integration.py -v
```

---

## 🧠 System Architecture & Mechanism Design

### Decentralized Non-Cooperative Bidding inside a Cooperative Protocol
Fest Ops models individual fest committees (Cultural Night, Technical Fest, Sports, Literary Fest, Entrepreneurship) as self-interested rational agents seeking to maximize their own event turnout and sponsor visibility subject to strict budget constraints. 

These non-cooperative agents operate within a cooperatively designed sealed-bid first-price auction mechanism. When an auction is lost:
1. **Losers Pay Nothing**: Sealed first-price protocol charges only the winning bidder.
2. **Substitute Resource Fallback**: Losers automatically attempt to acquire listed substitutes (e.g., Open-Air Theatre as a fallback for Main Auditorium).
3. **Partial Fulfillment**: If no substitute exists, the agent continues operations with reduced scope, feeding the fairness index.

### Centralized Hungarian Algorithm Benchmark
To evaluate the quality of the decentralized mechanism, Role C computes a centralized-optimal assignment using `scipy.optimize.linear_sum_assignment` on the committee valuation matrix. The ratio of decentralized obtained utility to theoretical centralized maximum utility yields the **Allocation Efficiency**.

---

## 📂 Repository Structure

```
FestOps/
├── agents/
│   ├── committee_agent.py          # Role A: Real CommitteeAgent & valuation logic
│   └── __init__.py
├── core/
│   ├── messages.py                 # Shared team contract: Bid, AuctionResult, DisruptionEvent
│   ├── metrics.py                  # Role A: Allocation efficiency, Jain's fairness, recovery time
│   ├── simulator.py                # Role D: Discrete-round orchestration engine
│   └── __init__.py
├── config/
│   ├── committees.yaml             # Role A: 5 distinct committee configurations
│   ├── resources.yaml              # Role A: Campus venues, equipment, volunteer pools
│   ├── scenario_default.yaml       # Role D: Baseline scenario (0% disruption)
│   └── scenario_disruption.yaml    # Role D: Shock scenario (35% disruption)
├── demo/
│   ├── app.py                      # Role D: Streamlit live demo shell
│   ├── committee_panel.py          # Role A: Streamlit committee display
│   └── __init__.py
├── stubs/                          # Temporary mocks standing in for pending B/C branches
│   ├── auctioneer_agent.py         # Role B Mock: Sealed-bid auctioneer
│   ├── disruption_agent.py         # Role C Mock: Stochastic and forced disruptions
│   ├── baseline.py                 # Role C Mock: Hungarian optimal assignment
│   ├── demo_panels.py              # Role B & C Mock: Streamlit panels
│   └── __init__.py
├── tests/
│   ├── test_committee_agent.py     # Role A: 44 unit tests
│   ├── test_integration.py         # Role D: End-to-end integration tests
│   └── __init__.py
├── main.py                         # Role D: CLI simulation entry point
├── pytest.ini                      # Pytest configuration
├── requirements.txt                # Locked environment dependencies
└── README.md                       # Role D: Project documentation
```

---

## 👥 Team & Role Responsibilities

- **Role A**: Committee Agent, Valuation Function, Fairness Metrics (`committees.yaml`, `resources.yaml`)
- **Role B**: Auctioneer Agent, Sealed First-Price Mechanism, Tiebreaking Protocol
- **Role C**: Algorithmic Modeling (Hungarian Baseline), Disruption Agent & Shock Analysis
- **Role D**: Simulator Orchestration, CLI Entry Point, Scenario Configs, Live Demo Shell, Integration Testing

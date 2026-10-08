"""
demo/app.py
===========
Role D — Live Interactive Streamlit Demonstration Shell for Fest Ops

Orchestration dashboard integrating:
- Role A Panel (Real): Committee configurations, valuations, and current bids
- Role B Panel (Stub): Sealed-bid auction mechanism outcomes
- Role C Panel (Stub): Hungarian baseline comparison, fairness, and disruption metrics
- Role D Shell: Discrete-round controls, step progression, and manual shock injection
"""

from __future__ import annotations

from pathlib import Path
import random
import sys
from typing import Any

# Ensure project root is in sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st
import pandas as pd

from agents.committee_agent import CommitteeAgent
from core.simulator import Simulator
from main import load_yaml

# Real panels from all roles
from demo.committee_panel import render_committee_panel  # Role A
from demo.auction_panel import render_auction_panel      # Role B
from demo.metrics_panel import render_metrics_panel      # Role C

# Real agents
from agents.auctioneer_agent import AuctioneerAgent      # Role B
from agents.disruption_agent import DisruptionAgent      # Role C


# ---------------------------------------------------------------------------
# Page Configuration & Styling
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Fest Ops — Multi-Agent Resource Allocation",
    page_icon="🎪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for rich aesthetics and clean typography
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    .metric-card {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.01));
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .status-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.82rem;
        font-weight: 600;
        margin-right: 6px;
    }
    .badge-real { background-color: #0e6251; color: #a3e4d7; }
    .badge-stub { background-color: #7d6608; color: #f9e79f; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Simulation Initialization in Session State
# ---------------------------------------------------------------------------

def init_simulation(scenario_rel_path: str = "config/scenario_default.yaml") -> Simulator:
    """Initialize a new Simulator instance and cache it in st.session_state."""
    scenario_path = project_root / scenario_rel_path
    scenario = load_yaml(scenario_path)

    committees_file = project_root / scenario.get("committees_file", "config/committees.yaml")
    resources_file = project_root / scenario.get("resources_file", "config/resources.yaml")

    committees_raw = load_yaml(committees_file).get("committees", [])
    resources_raw = load_yaml(resources_file).get("resources", [])

    seed = scenario.get("seed", 42)
    rng = random.Random(seed)

    # Real Role A CommitteeAgents
    committees = [
        CommitteeAgent(
            committee_id=c["id"],
            budget=float(c["budget"]),
            priorities=dict(c["priorities"]),
            wanted_resources=list(c["wanted_resources"]),
            substitutes=dict(c.get("substitutes", {})),
            rng=random.Random(rng.randint(0, 100_000)),
        )
        for c in committees_raw
    ]

    # Stubs for Role B & Role C
    auctioneer = AuctioneerAgent(rng=random.Random(rng.randint(0, 100_000)))
    disruption_agent = DisruptionAgent(
        probability=float(scenario.get("disruption_probability", 0.0)),
        rng=random.Random(rng.randint(0, 100_000)),
    )

    sim = Simulator(
        committees=committees,
        resources=resources_raw,
        auctioneer=auctioneer,
        disruption_agent=disruption_agent,
        seed=seed,
    )
    return sim


# Initialize state containers
if "sim" not in st.session_state:
    st.session_state.selected_scenario = "config/scenario_default.yaml"
    st.session_state.sim = init_simulation(st.session_state.selected_scenario)
    st.session_state.state = st.session_state.sim.get_state()
    st.session_state.last_action = "Simulation initialized."


# ---------------------------------------------------------------------------
# Sidebar Controls & Architecture Status
# ---------------------------------------------------------------------------

with st.sidebar:
    st.title("🎪 Fest Ops")
    st.caption("23CSE401 Foundations of AI — Case Study")
    st.markdown("Decentralized Multi-Agent Auction with Stochastic Disruptions")
    st.divider()

    st.subheader("⚙️ Scenario Configuration")
    scenario_choice = st.selectbox(
        "Select Scenario",
        options=["config/scenario_default.yaml", "config/scenario_disruption.yaml"],
        format_func=lambda x: "🟢 Default (0% Disruption)" if "default" in x else "⚡ Disruption (35% Disruption)",
        key="scenario_select",
    )

    if scenario_choice != st.session_state.selected_scenario:
        st.session_state.selected_scenario = scenario_choice
        st.session_state.sim = init_simulation(scenario_choice)
        st.session_state.state = st.session_state.sim.get_state()
        st.session_state.last_action = f"Switched to {scenario_choice} and reset."
        st.rerun()

    st.divider()

    st.subheader("🕹️ Simulation Controls")

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("▶️ Run 1 Round", key="btn_run_round", use_container_width=True):
            st.session_state.state = st.session_state.sim.step()
            st.session_state.last_action = f"Advanced to Round {st.session_state.sim.round_num}."
            st.rerun()

    with col_btn2:
        if st.button("⏩ Run 5 Rounds", key="btn_run_5_rounds", use_container_width=True):
            for _ in range(5):
                st.session_state.state = st.session_state.sim.step()
            st.session_state.last_action = f"Fast-forwarded 5 rounds to Round {st.session_state.sim.round_num}."
            st.rerun()

    if st.button("🔄 Reset Simulation", key="btn_reset", use_container_width=True):
        st.session_state.sim = init_simulation(st.session_state.selected_scenario)
        st.session_state.state = st.session_state.sim.get_state()
        st.session_state.last_action = "Simulation reset to Round 0."
        st.rerun()

    st.divider()

    st.subheader("⚡ Manual Shock Injection")
    st.caption("Trigger forced disruption on demand to demo decentralized recovery.")

    # List resources currently held by any committee
    currently_held = [
        res for c in st.session_state.sim.committees for res in c.allocated_resources
    ]
    target_options = currently_held if currently_held else st.session_state.sim.resource_ids

    target_res = st.selectbox(
        "Target Resource",
        options=target_options,
        key="target_disrupt_res",
    )

    if st.button("🚨 Trigger Disruption Now", key="btn_trigger_disruption", type="primary", use_container_width=True):
        if st.session_state.sim.round_num == 0:
            st.warning("Please run at least one round before triggering a disruption.")
        else:
            event = st.session_state.sim.force_disruption(resource_id=target_res)
            st.session_state.state = st.session_state.sim.get_state()
            st.session_state.last_action = f"Forced disruption on '{event.resource_id}' ({event.reason})."
            st.rerun()

    st.divider()

    st.subheader("🧩 Architecture Status")
    st.markdown('<span class="status-badge badge-real">Role A: Real</span> Committees & Metrics', unsafe_allow_html=True)
    st.markdown('<span class="status-badge badge-real">Role B: Real</span> Auctioneer Mechanism', unsafe_allow_html=True)
    st.markdown('<span class="status-badge badge-real">Role C: Real</span> Disruption & Hungarian', unsafe_allow_html=True)
    st.markdown('<span class="status-badge badge-real">Role D: Real</span> Simulator & Demo Shell', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Main Dashboard Hero & KPIs
# ---------------------------------------------------------------------------

state = st.session_state.state
sim = st.session_state.sim

st.title("🎪 Fest Ops — Campus Resource Allocation")
st.caption(f"Status: {st.session_state.last_action}")

# Top KPI Summary Cards
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
metrics = state.get("metrics", {})

eff = metrics.get("allocation_efficiency", 0.0)
fair = metrics.get("fairness_index", 1.0)
util = metrics.get("resource_utilization", 0.0)
active_alloc = len({r for c in sim.committees for r in c.allocated_resources})
total_res = len(sim.resources)

with kpi1:
    st.metric("Round Number", value=f"{sim.round_num}")
with kpi2:
    st.metric("Allocation Efficiency", value=f"{eff * 100:.1f}%")
with kpi3:
    st.metric("Fairness (Jain's)", value=f"{fair:.3f}")
with kpi4:
    st.metric("Resource Utilization", value=f"{util * 100:.0f}%", delta=f"{active_alloc}/{total_res} used")
with kpi5:
    st.metric("Total Disruptions", value=f"{len(sim.disruptions_log)}")

st.divider()


# ---------------------------------------------------------------------------
# Multi-Panel Tabs (Role A Real + Role B Stub + Role C Stub + Role D Log)
# ---------------------------------------------------------------------------

tab1, tab2, tab3, tab4 = st.tabs([
    "🎭 Committees (Role A)",
    "🔨 Auction Mechanism (Role B)",
    "📊 Metrics & Baseline (Role C)",
    "📜 Simulation Log & Trajectory (Role D)",
])

with tab1:
    # Real Role A panel
    render_committee_panel(state)

with tab2:
    # Real Role B panel
    render_auction_panel(state)

with tab3:
    # Real Role C panel
    render_metrics_panel(state)

with tab4:
    st.header("📜 Simulation History & Trajectory — Role D")
    if not sim.log.empty:
        st.subheader("📈 Round-by-Round Log")
        st.dataframe(sim.log, use_container_width=True)

        st.subheader("⚡ Event Stream")
        if sim.events:
            st.dataframe(pd.DataFrame(sim.events), use_container_width=True)
        else:
            st.caption("No events recorded.")
    else:
        st.info("Simulation has not started yet. Click 'Run 1 Round' in the sidebar to begin.")

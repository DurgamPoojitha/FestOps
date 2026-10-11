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
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS inspired by reference UI: Plus Jakarta Sans, Mint Canvas, Deep Teal, Amber CTA
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');

    /* Global Application Canvas */
    .stApp {
        background: #edf8f6 !important;
        background-image: radial-gradient(circle at 12% 15%, rgba(126, 226, 217, 0.25) 0%, transparent 45%),
                          radial-gradient(circle at 88% 85%, rgba(0, 109, 100, 0.08) 0%, transparent 50%) !important;
        font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, sans-serif !important;
        color: #0f332f !important;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 700 !important;
        color: #005952 !important;
        letter-spacing: -0.02em !important;
    }

    p, span, label, div {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }

    /* Sidebar Canvas & Styling */
    section[data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid rgba(0, 109, 100, 0.12) !important;
        box-shadow: 4px 0 20px rgba(0, 89, 82, 0.03) !important;
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #005952 !important;
    }

    /* Branded Hero Header Banner matching reference card */
    .fest-hero {
        background: linear-gradient(135deg, #004d47 0%, #00665e 55%, #00776d 100%);
        color: #ffffff;
        padding: 30px 36px;
        border-radius: 20px;
        margin-bottom: 24px;
        box-shadow: 0 12px 36px -6px rgba(0, 77, 71, 0.35);
        position: relative;
        overflow: hidden;
    }
    .fest-hero-ribbon {
        position: absolute;
        right: 130px;
        top: -20px;
        width: 220px;
        height: 160px;
        pointer-events: none;
        opacity: 0.25;
    }
    .fest-hero-rocket {
        position: absolute;
        right: 32px;
        bottom: 0px;
        width: 120px;
        height: 130px;
        pointer-events: none;
    }
    .fest-badge-bar {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 12px;
    }
    .fest-cap-icon {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        background: #ffffff;
        color: #005952;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.12);
    }
    .fest-sub-tag {
        font-size: 0.95rem;
        font-weight: 700;
        color: #ffffff;
        letter-spacing: 0.01em;
    }
    .fest-course-badge {
        font-size: 0.72rem;
        font-weight: 700;
        background: rgba(255, 255, 255, 0.18);
        color: #ffffff;
        padding: 4px 12px;
        border-radius: 14px;
        letter-spacing: 0.05em;
        border: 1px solid rgba(255, 255, 255, 0.25);
    }
    .fest-title {
        font-size: 2.2rem;
        font-weight: 800;
        margin: 0 0 8px 0;
        letter-spacing: -0.025em;
        color: #ffffff !important;
    }
    .fest-desc {
        font-size: 0.98rem;
        color: #bbf2eb;
        margin: 0 0 16px 0;
        max-width: 680px;
        line-height: 1.5;
    }
    .fest-status-pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 6px 16px;
        background: rgba(0, 0, 0, 0.22);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 9999px;
        font-size: 0.82rem;
        color: #e6fffa;
        backdrop-filter: blur(4px);
    }
    .fest-status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #34d399;
        display: inline-block;
        box-shadow: 0 0 8px #34d399;
    }

    /* Floating White Metric KPI Cards */
    div[data-testid="stMetric"] {
        background: #ffffff !important;
        border: 1px solid rgba(0, 109, 100, 0.14) !important;
        border-radius: 18px !important;
        padding: 16px 20px !important;
        box-shadow: 0 6px 20px rgba(0, 89, 82, 0.05) !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
    }
    div[data-testid="stMetric"]:hover {
        border-color: #006d64 !important;
        transform: translateY(-2px);
        box-shadow: 0 10px 24px rgba(0, 89, 82, 0.1) !important;
    }
    div[data-testid="stMetricLabel"] {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 700 !important;
        font-size: 0.78rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        color: #006d64 !important;
    }
    div[data-testid="stMetricValue"] {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 800 !important;
        font-size: 1.85rem !important;
        color: #09332f !important;
    }

    /* Primary Accent Button: Warm Amber / Orange (Matches "Request a Demo" in reference image) */
    button[kind="primary"], .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #f57c28 0%, #ea580c 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 9999px !important;
        padding: 0.6rem 1.6rem !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        box-shadow: 0 6px 18px rgba(234, 88, 12, 0.35) !important;
        transition: all 0.2s ease-in-out !important;
    }
    button[kind="primary"]:hover, .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 24px rgba(234, 88, 12, 0.45) !important;
    }

    /* Secondary Control Buttons (Pill-shaped with crisp teal borders) */
    button[kind="secondary"], .stButton > button:not([kind="primary"]) {
        background: #ffffff !important;
        border-radius: 9999px !important;
        border: 1.5px solid #006d64 !important;
        color: #006d64 !important;
        font-weight: 700 !important;
        font-size: 0.9rem !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        box-shadow: 0 2px 8px rgba(0, 109, 100, 0.06) !important;
        transition: all 0.2s ease-in-out !important;
    }
    button[kind="secondary"]:hover, .stButton > button:not([kind="primary"]):hover {
        border-color: #005952 !important;
        background: #edf8f6 !important;
        color: #004d47 !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(0, 109, 100, 0.12) !important;
    }

    /* Floating Segmented Tabs */
    div[data-testid="stTabs"] [data-baseweb="tab-list"] {
        background: #ffffff !important;
        padding: 6px 10px !important;
        border-radius: 16px !important;
        border: 1px solid rgba(0, 109, 100, 0.12) !important;
        box-shadow: 0 4px 16px rgba(0, 89, 82, 0.05) !important;
        gap: 8px !important;
        margin-bottom: 20px !important;
    }
    div[data-testid="stTabs"] button {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.92rem !important;
        border-radius: 12px !important;
        padding: 8px 18px !important;
        color: #4a6864 !important;
        border: none !important;
        transition: all 0.2s ease !important;
    }
    div[data-testid="stTabs"] button[aria-selected="true"] {
        background: #006d64 !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 12px rgba(0, 109, 100, 0.28) !important;
    }

    /* Card Expander containers */
    div[data-testid="stExpander"] {
        background: #ffffff !important;
        border: 1px solid rgba(0, 109, 100, 0.12) !important;
        border-radius: 16px !important;
        box-shadow: 0 4px 16px rgba(0, 89, 82, 0.04) !important;
        margin-bottom: 12px !important;
        overflow: hidden;
    }
    div[data-testid="stExpander"] summary {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 700 !important;
        color: #005952 !important;
    }

    /* Dataframe & Tables */
    div[data-testid="stDataFrame"] {
        background: #ffffff !important;
        border-radius: 14px !important;
        border: 1px solid rgba(0, 109, 100, 0.12) !important;
        overflow: hidden;
        box-shadow: 0 2px 10px rgba(0, 89, 82, 0.03) !important;
    }

    /* Architecture Badges */
    .status-badge {
        display: inline-block;
        padding: 5px 12px;
        border-radius: 14px;
        font-size: 0.8rem;
        font-weight: 700;
        margin-right: 6px;
        letter-spacing: 0.02em;
    }
    .badge-real { background-color: #006d64; color: #ffffff; box-shadow: 0 2px 6px rgba(0, 109, 100, 0.2); }
    .badge-stub { background-color: #ea580c; color: #ffffff; }
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
    st.title("Fest Ops")
    st.caption("23CSE401 Foundations of AI — Case Study")
    st.markdown("Decentralized Multi-Agent Auction with Stochastic Disruptions")
    st.divider()

    st.subheader("Scenario Configuration")
    scenario_choice = st.selectbox(
        "Select Scenario",
        options=["config/scenario_default.yaml", "config/scenario_disruption.yaml"],
        format_func=lambda x: "Default (0% Disruption)" if "default" in x else "Disruption (35% Disruption)",
        key="scenario_select",
    )

    if scenario_choice != st.session_state.selected_scenario:
        st.session_state.selected_scenario = scenario_choice
        st.session_state.sim = init_simulation(scenario_choice)
        st.session_state.state = st.session_state.sim.get_state()
        st.session_state.last_action = f"Switched to {scenario_choice} and reset."
        st.rerun()

    st.divider()

    st.subheader("Simulation Controls")

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("Run 1 Round", key="btn_run_round", use_container_width=True):
            st.session_state.state = st.session_state.sim.step()
            st.session_state.last_action = f"Advanced to Round {st.session_state.sim.round_num}."
            st.rerun()

    with col_btn2:
        if st.button("Run 5 Rounds", key="btn_run_5_rounds", use_container_width=True):
            for _ in range(5):
                st.session_state.state = st.session_state.sim.step()
            st.session_state.last_action = f"Fast-forwarded 5 rounds to Round {st.session_state.sim.round_num}."
            st.rerun()

    if st.button("Reset Simulation", key="btn_reset", use_container_width=True):
        st.session_state.sim = init_simulation(st.session_state.selected_scenario)
        st.session_state.state = st.session_state.sim.get_state()
        st.session_state.last_action = "Simulation reset to Round 0."
        st.rerun()

    st.divider()

    st.subheader("Manual Shock Injection")
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

    if st.button("Trigger Disruption Now", key="btn_trigger_disruption", type="primary", use_container_width=True):
        if st.session_state.sim.round_num == 0:
            st.warning("Please run at least one round before triggering a disruption.")
        else:
            event = st.session_state.sim.force_disruption(resource_id=target_res)
            st.session_state.state = st.session_state.sim.get_state()
            st.session_state.last_action = f"Forced disruption on '{event.resource_id}' ({event.reason})."
            st.rerun()

    st.divider()

    st.subheader("Architecture Status")
    st.markdown('<span class="status-badge badge-real">Role A: Real</span> Committees & Metrics', unsafe_allow_html=True)
    st.markdown('<span class="status-badge badge-real">Role B: Real</span> Auctioneer Mechanism', unsafe_allow_html=True)
    st.markdown('<span class="status-badge badge-real">Role C: Real</span> Disruption & Hungarian', unsafe_allow_html=True)
    st.markdown('<span class="status-badge badge-real">Role D: Real</span> Simulator & Demo Shell', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Main Dashboard Hero & KPIs
# ---------------------------------------------------------------------------

state = st.session_state.state
sim = st.session_state.sim

# Branded Hero Banner reflecting the Camms.College reference styling
st.markdown(
    f"""
    <div class="fest-hero">
        <svg class="fest-hero-ribbon" viewBox="0 0 260 160" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M40 150 C 60 50, 180 30, 220 85 C 250 130, 180 160, 125 115 C 75 75, 115 15, 210 10" stroke="#7fe5dc" stroke-width="26" stroke-linecap="round" fill="none"/>
        </svg>
        <svg class="fest-hero-rocket" viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M60 18 C60 18 73 34 73 60 L47 60 C47 34 60 18 60 18Z" fill="#ffffff"/>
            <circle cx="60" cy="38" r="5" fill="#006d64"/>
            <path d="M47 52 L36 65 L47 63 Z" fill="#7fe5dc"/>
            <path d="M73 52 L84 65 L73 63 Z" fill="#7fe5dc"/>
            <path d="M57 60 L63 60 L60 80 Z" fill="#f57c28"/>
            <path d="M16 112 C16 98 30 92 38 98 C44 87 60 87 66 96 C72 90 88 91 92 102 C100 102 106 108 104 114 Z" fill="#ffffff" opacity="0.95"/>
        </svg>
        <div class="fest-badge-bar">
            <div class="fest-cap-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M22 10v6M2 10l10-5 10 5-10 5z"/>
                    <path d="M6 12v5c3 3 9 3 12 0v-5"/>
                </svg>
            </div>
            <span class="fest-sub-tag">FestOps Platform</span>
            <span class="fest-course-badge">23CSE401 Foundations of AI</span>
        </div>
        <div class="fest-title">Campus Resource Allocation</div>
        <div class="fest-desc">Decentralized multi-agent sealed-bid auction mechanism with stochastic disruption simulation and Kuhn-Munkres benchmark tracking.</div>
        <div class="fest-status-pill">
            <span class="fest-status-dot"></span>
            <span>Status: {st.session_state.last_action}</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

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
    "Committees (Role A)",
    "Auction Mechanism (Role B)",
    "Metrics & Baseline (Role C)",
    "Simulation Log & Trajectory (Role D)",
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
    st.markdown(
        """
        <div style="display: flex; align-items: center; gap: 14px; margin-bottom: 8px;">
            <div style="width: 42px; height: 42px; border-radius: 50%; background: #006d64; display: flex; align-items: center; justify-content: center; color: #ffffff; box-shadow: 0 4px 12px rgba(0, 109, 100, 0.25);">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                    <polyline points="14 2 14 8 20 8"></polyline>
                    <line x1="16" y1="13" x2="8" y2="13"></line>
                    <line x1="16" y1="17" x2="8" y2="17"></line>
                    <polyline points="10 9 9 9 8 9"></polyline>
                </svg>
            </div>
            <div>
                <h2 style="margin: 0; color: #005952; font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 700; font-size: 1.5rem;">Simulation History & Trajectory — Role D</h2>
                <span style="font-size: 0.85rem; color: #4a6864;">Full trajectory timeline, round logs, and discrete-event audit stream</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if not sim.log.empty:
        st.subheader("Round-by-Round Log")
        st.dataframe(sim.log, use_container_width=True)

        st.subheader("Event Stream")
        if sim.events:
            st.dataframe(pd.DataFrame(sim.events), use_container_width=True)
        else:
            st.caption("No events recorded.")
    else:
        st.info("Simulation has not started yet. Click 'Run 1 Round' in the sidebar to begin.")

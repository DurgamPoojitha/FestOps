"""
stubs/demo_panels.py
====================
TEMPORARY STUB PANELS — Standing in for Role B and Role C Streamlit panels.
Each panel matches the agreed team signature:
    render_x_panel(state: dict) -> None

SWAP NOTICE:
Once Role B and Role C provide their panel files:
    - Swap render_auction_panel with `from demo.auction_panel import render_auction_panel`
    - Swap render_metrics_panel with `from demo.metrics_panel import render_metrics_panel`
"""

from __future__ import annotations

from typing import Any
import streamlit as st


def render_auction_panel(state: dict) -> None:
    """
    Placeholder panel for Role B (Auction Mechanism).

    Parameters
    ----------
    state : dict
        Shared simulation state from Role D's Simulator.
    """
    st.header("🔨 Auction Room — Role B Panel")
    st.info("📌 **Auction panel — pending Role B.** Displaying interim simulation auction feeds below.")

    current_round = state.get("round")
    if current_round is not None:
        st.caption(f"**Auction Round:** {current_round}")

    auction_results: list[Any] = state.get("auction_results", [])
    if auction_results:
        st.subheader("🏆 Round Auction Outcomes")
        rows = []
        for res in auction_results:
            rows.append({
                "Resource": getattr(res, "resource_id", res.get("resource_id", "—") if isinstance(res, dict) else "—"),
                "Winner": getattr(res, "winner_id", res.get("winner_id", "Unallocated") if isinstance(res, dict) else "Unallocated") or "Unallocated",
                "Winning Bid (₹)": getattr(res, "winning_bid", res.get("winning_bid", 0.0) if isinstance(res, dict) else 0.0),
                "Losers": ", ".join(getattr(res, "losers", res.get("losers", []) if isinstance(res, dict) else [])) or "None",
            })
        st.dataframe(rows, use_container_width=True)
    else:
        st.caption("No contested auction results recorded for this step.")


def render_metrics_panel(state: dict) -> None:
    """
    Placeholder panel for Role C (Algorithmic Modeling, Hungarian Baseline & Disruption).

    Parameters
    ----------
    state : dict
        Shared simulation state from Role D's Simulator.
    """
    st.header("📊 Metrics & Resilience — Role C Panel")
    st.info("📌 **Metrics panel — pending Role C.** Displaying interim metrics and baseline comparisons below.")

    metrics: dict[str, Any] = state.get("metrics", {})
    col1, col2, col3 = st.columns(3)

    efficiency = metrics.get("allocation_efficiency", 0.0)
    fairness = metrics.get("fairness_index", 1.0)
    utilization = metrics.get("resource_utilization", 0.0)

    with col1:
        st.metric(
            label="Allocation Efficiency",
            value=f"{efficiency * 100:.1f}%",
            help="Decentralized utility divided by centralized theoretical maximum",
        )
    with col2:
        st.metric(
            label="Jain's Fairness Index",
            value=f"{fairness:.3f}",
            help="Fairness of allocation across all committees (1.0 = perfectly fair)",
        )
    with col3:
        st.metric(
            label="Resource Utilization",
            value=f"{utilization * 100:.1f}%",
            help="Percentage of available resources currently allocated",
        )

    disruptions: list[dict] = state.get("disruptions", [])
    if disruptions:
        st.subheader("⚡ Disruption Log")
        st.dataframe(disruptions, use_container_width=True)
    else:
        st.caption("No disruptions logged yet.")

"""
demo/metrics_panel.py
=====================
Role C — Streamlit metrics panel for algorithmic baseline comparison and disruption recovery.

Exposes:
    render_metrics_panel(state: dict) -> None
"""

from __future__ import annotations

from typing import Any
import pandas as pd
import streamlit as st


def render_metrics_panel(state: dict) -> None:
    """
    Render the Role C metrics panel inside the Streamlit dashboard.

    Displays:
    - Allocation Efficiency (Decentralized vs. Centralized Hungarian Baseline)
    - Jain's Fairness Index & Resource Utilization
    - Decentralized vs. Centralized Benchmark Chart
    - Disruption & Recovery Tracking
    """
    st.header("📊 Metrics & Baseline Comparison — Role C Panel")

    current_round = state.get("round")
    if current_round is not None:
        st.caption(f"**Simulation Round:** {current_round}")

    metrics: dict[str, Any] = state.get("metrics", {})
    efficiency = float(metrics.get("allocation_efficiency", 0.0))
    fairness = float(metrics.get("fairness_index", 1.0))
    utilization = float(metrics.get("resource_utilization", 0.0))
    obtained_utility = float(metrics.get("obtained_utility", 0.0))
    max_utility = float(metrics.get("max_utility", 0.0))

    # 1. Primary Metrics Row
    mcol1, mcol2, mcol3, mcol4 = st.columns(4)
    with mcol1:
        st.metric(
            label="Allocation Efficiency",
            value=f"{efficiency * 100:.1f}%",
            help="Decentralized utility achieved / Centralized Hungarian theoretical optimal",
        )
    with mcol2:
        st.metric(
            label="Jain's Fairness Index",
            value=f"{fairness:.3f}",
            help="Fairness metric across all committee utility allocations (1.0 = equal)",
        )
    with mcol3:
        st.metric(
            label="Resource Utilization",
            value=f"{utilization * 100:.1f}%",
            help="Fraction of available campus resources successfully awarded",
        )
    with mcol4:
        st.metric(
            label="Won vs Optimal Utility",
            value=f"{obtained_utility:,.0f} / {max_utility:,.0f}",
            help="Decentralized achieved utility vs. Centralized Hungarian baseline maximum",
        )

    st.divider()

    # 2. Algorithmic Baseline Comparison (Rubric Line Item)
    st.subheader("⚖️ Algorithmic Modeling: Decentralized vs. Hungarian Baseline")
    st.markdown(
        "Comparison of decentralized sealed-bid auction performance against the "
        "centralized theoretical optimum computed via the **Hungarian Algorithm** "
        "(`scipy.optimize.linear_sum_assignment`)."
    )

    if max_utility > 0:
        chart_data = pd.DataFrame({
            "Mechanism": ["Decentralized Auction", "Centralized Hungarian Optimal"],
            "Total Social Welfare (Utility)": [obtained_utility, max_utility],
        })
        st.bar_chart(
            chart_data.set_index("Mechanism"),
            use_container_width=True,
            color=["#3498db"],
        )
    else:
        st.info("Run at least one simulation round to visualize welfare comparison.")

    st.divider()

    # 3. Disruption & Recovery Tracking
    st.subheader("⚡ Environmental Disruptions & Resilience")
    disruptions: list[dict] = state.get("disruptions", [])
    events: list[dict] = state.get("events", [])

    if disruptions:
        d_rows = []
        for d in disruptions:
            d_round = d.get("round", -1)
            res_id = d.get("resource_id", "—")
            comm_id = d.get("committee_id", "—")
            reason = d.get("reason", "unknown")

            # Check if recovery occurred
            recovery_round = None
            for e in events:
                if (
                    e.get("event") == "reallocated"
                    and e.get("resource_id") == res_id
                    and e.get("committee_id") == comm_id
                    and e.get("round", -1) > d_round
                ):
                    recovery_round = e.get("round")
                    break

            rec_time_str = f"{recovery_round - d_round} round(s)" if recovery_round else "Pending / Unrecovered"
            d_rows.append({
                "Disruption Round": d_round,
                "Resource": res_id,
                "Affected Committee": comm_id,
                "Cause": reason.replace("_", " ").title(),
                "Recovery Status": rec_time_str,
            })

        st.dataframe(d_rows, use_container_width=True)
    else:
        st.caption("No environmental disruptions recorded yet.")

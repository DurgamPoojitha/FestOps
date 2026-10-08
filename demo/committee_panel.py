"""
demo/committee_panel.py
=======================
Role A — Streamlit panel for committee information.

This module exposes exactly ONE public function:

    render_committee_panel(state: dict) -> None

It is a self-contained panel — it does NOT call st.set_page_config(),
and it does NOT know about other panels.

Role D's demo/app.py will call this function as part of the full dashboard:

    from demo.committee_panel import render_committee_panel
    render_committee_panel(state)

Expected `state` keys (all optional — missing keys are handled gracefully)
--------------------------------------------------------------------------
"committees" : list[dict]
    Each dict is the output of CommitteeAgent.get_state(), i.e.:
    {
        "id": str,
        "budget": float,
        "remaining_budget": float,
        "priorities": dict[str, float],
        "wanted_resources": list[str],
        "allocated_resources": list[str],
        "partial_fulfillment": list[str],
    }

"bids" : list[dict]
    Each dict represents one bid:
    {
        "committee_id": str,
        "resource_id": str,
        "amount": float,
    }

"round" : int
    Current simulation round number.
"""

from __future__ import annotations

from typing import Any

import streamlit as st


def render_committee_panel(state: dict) -> None:
    """
    Render the Role A committee panel inside a Streamlit app.

    Reads whatever it needs from ``state`` using defensive ``.get()`` calls
    so that missing optional fields never crash the panel.

    Parameters
    ----------
    state : dict
        Shared simulation state produced by Role D's Simulator and passed
        to all panel functions.

    Returns
    -------
    None
        All output is produced via ``st.*`` calls.
    """
    st.header("🎭 Committees — Role A Panel")

    # -- Round indicator ------------------------------------------------------
    current_round = state.get("round")
    if current_round is not None:
        st.caption(f"**Simulation Round:** {current_round}")

    # -- Committee cards -------------------------------------------------------
    committees: list[dict] = state.get("committees", [])

    if not committees:
        st.info("No committee data available yet. Run a simulation round first.")
    else:
        for committee in committees:
            _render_single_committee(committee)

    # -- Bids table -----------------------------------------------------------
    bids: list[dict] = state.get("bids", [])
    if bids:
        st.subheader("📋 Current Round Bids")
        _render_bids_table(bids)
    else:
        st.subheader("📋 Bids")
        st.caption("No bids submitted yet for this round.")


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _render_single_committee(committee: dict) -> None:
    """
    Render one committee's card using a Streamlit expander.

    Parameters
    ----------
    committee : dict
        Output of CommitteeAgent.get_state().
    """
    committee_id = committee.get("id", "Unknown Committee")

    with st.expander(f"**{committee_id.replace('_', ' ').title()}**", expanded=False):

        # -- Budget -----------------------------------------------------------
        col1, col2 = st.columns(2)

        total_budget = committee.get("budget", 0.0)
        remaining = committee.get("remaining_budget", 0.0)
        spent = total_budget - remaining

        with col1:
            st.metric(label="Total Budget (₹)", value=f"{total_budget:,.0f}")
            st.metric(label="Remaining Budget (₹)", value=f"{remaining:,.0f}",
                      delta=f"-{spent:,.0f}" if spent > 0 else None,
                      delta_color="inverse")

        with col2:
            # Budget bar
            if total_budget > 0:
                utilised_pct = (spent / total_budget) * 100
                st.metric(label="Budget Used", value=f"{utilised_pct:.1f}%")
            else:
                st.metric(label="Budget Used", value="N/A")

        st.divider()

        # -- Priorities -------------------------------------------------------
        priorities: dict = committee.get("priorities", {})
        if priorities:
            st.markdown("**🎯 Priorities**")
            pcols = st.columns(len(priorities))
            for i, (key, val) in enumerate(priorities.items()):
                pcols[i].metric(label=key.replace("_", " ").title(), value=f"{val:.2f}")

        st.divider()

        # -- Resources --------------------------------------------------------
        rcol1, rcol2, rcol3 = st.columns(3)

        with rcol1:
            st.markdown("**🎫 Wanted**")
            wanted: list[str] = committee.get("wanted_resources", [])
            if wanted:
                for r in wanted:
                    st.write(f"• {r}")
            else:
                st.write("—")

        with rcol2:
            st.markdown("**✅ Allocated**")
            allocated: list[str] = committee.get("allocated_resources", [])
            if allocated:
                for r in allocated:
                    st.success(r)
            else:
                st.write("—")

        with rcol3:
            st.markdown("**⚠️ Partial Fulfillment**")
            partial: list[str] = committee.get("partial_fulfillment", [])
            if partial:
                for r in partial:
                    st.warning(r)
            else:
                st.write("—")


def _render_bids_table(bids: list[dict]) -> None:
    """
    Render bid data as a formatted Streamlit table.

    Parameters
    ----------
    bids : list[dict]
        Each dict has keys: committee_id, resource_id, amount.
    """
    # Build display rows
    rows: list[dict[str, Any]] = []
    for bid in bids:
        rows.append({
            "Committee": bid.get("committee_id", "—"),
            "Resource": bid.get("resource_id", "—"),
            "Bid Amount (₹)": bid.get("amount", 0.0),
        })

    if rows:
        # Sort by bid amount descending so highest bids are visible first
        rows.sort(key=lambda x: x["Bid Amount (₹)"], reverse=True)

        # Highlight the top bid per resource
        st.dataframe(
            rows,
            use_container_width=True,
            column_config={
                "Bid Amount (₹)": st.column_config.NumberColumn(
                    format="₹%.2f"
                )
            },
        )

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
    st.markdown(
        """
        <div style="display: flex; align-items: center; gap: 14px; margin-bottom: 8px;">
            <div style="width: 42px; height: 42px; border-radius: 50%; background: #006d64; display: flex; align-items: center; justify-content: center; color: #ffffff; box-shadow: 0 4px 12px rgba(0, 109, 100, 0.25);">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                    <circle cx="9" cy="7" r="4"></circle>
                    <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
                    <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                </svg>
            </div>
            <div>
                <h2 style="margin: 0; color: #005952; font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 700; font-size: 1.5rem;">Committees — Role A Panel</h2>
                <span style="font-size: 0.85rem; color: #4a6864;">Committee valuation profiles, strategic budget constraints, and active bids</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

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
        st.subheader("Current Round Bids")
        _render_bids_table(bids)
    else:
        st.subheader("Bids")
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
            st.markdown("**Priorities**")
            pcols = st.columns(len(priorities))
            for i, (key, val) in enumerate(priorities.items()):
                pcols[i].metric(label=key.replace("_", " ").title(), value=f"{val:.2f}")

        st.divider()

        # -- Resources --------------------------------------------------------
        rcol1, rcol2, rcol3 = st.columns(3)

        with rcol1:
            st.markdown("<p style='font-size: 0.82rem; font-weight: 700; color: #006d64; text-transform: uppercase; margin-bottom: 6px;'>Wanted Resources</p>", unsafe_allow_html=True)
            wanted: list[str] = committee.get("wanted_resources", [])
            if wanted:
                tags = "".join(f"<span style='display:inline-block; background:#e6f7f4; color:#005952; border:1px solid #bceae2; border-radius:14px; padding:3px 10px; font-size:0.8rem; font-weight:600; margin:2px 4px 2px 0;'>{r}</span>" for r in wanted)
                st.markdown(tags, unsafe_allow_html=True)
            else:
                st.write("—")

        with rcol2:
            st.markdown("<p style='font-size: 0.82rem; font-weight: 700; color: #006d64; text-transform: uppercase; margin-bottom: 6px;'>Allocated Resources</p>", unsafe_allow_html=True)
            allocated: list[str] = committee.get("allocated_resources", [])
            if allocated:
                tags = "".join(f"<span style='display:inline-block; background:#dcfce7; color:#166534; border:1px solid #bbf7d0; border-radius:14px; padding:3px 10px; font-size:0.8rem; font-weight:600; margin:2px 4px 2px 0;'>{r}</span>" for r in allocated)
                st.markdown(tags, unsafe_allow_html=True)
            else:
                st.write("—")

        with rcol3:
            st.markdown("<p style='font-size: 0.82rem; font-weight: 700; color: #006d64; text-transform: uppercase; margin-bottom: 6px;'>Partial Fulfillment</p>", unsafe_allow_html=True)
            partial: list[str] = committee.get("partial_fulfillment", [])
            if partial:
                tags = "".join(f"<span style='display:inline-block; background:#ffedd5; color:#c2410c; border:1px solid #fed7aa; border-radius:14px; padding:3px 10px; font-size:0.8rem; font-weight:600; margin:2px 4px 2px 0;'>{r}</span>" for r in partial)
                st.markdown(tags, unsafe_allow_html=True)
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

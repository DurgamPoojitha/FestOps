"""
demo/auction_panel.py
=====================
Role B — Streamlit auction panel rendering live auction results and bids.
"""

from __future__ import annotations

from typing import Any


def _value(item: Any, key: str, default: Any = None) -> Any:
    return item.get(key, default) if isinstance(item, dict) else getattr(item, key, default)


def render_auction_panel(state: dict) -> None:
    """Display available bids, outcomes, ties, and invalid bids from simulator state."""
    import streamlit as st

    st.markdown(
        """
        <div style="display: flex; align-items: center; gap: 14px; margin-bottom: 8px;">
            <div style="width: 42px; height: 42px; border-radius: 50%; background: #006d64; display: flex; align-items: center; justify-content: center; color: #ffffff; box-shadow: 0 4px 12px rgba(0, 109, 100, 0.25);">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect>
                    <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path>
                </svg>
            </div>
            <div>
                <h2 style="margin: 0; color: #005952; font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 700; font-size: 1.5rem;">Auction Room — Role B Panel</h2>
                <span style="font-size: 0.85rem; color: #4a6864;">Sealed-bid auction outcomes, clearing prices, and resource allocations</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    bids = state.get("bids", []) or []
    outcomes = state.get("auction_results", []) or []
    invalid = state.get("invalid_bids", []) or []
    bids_by_resource: dict[str, list[float]] = {}
    for bid in bids:
        try:
            bids_by_resource.setdefault(str(_value(bid, "resource_id")), []).append(
                float(_value(bid, "amount"))
            )
        except (TypeError, ValueError):
            continue
    if bids:
        st.subheader("Submitted Bids")
        st.dataframe([
            {"Committee": _value(b, "committee_id", "—"),
             "Resource": _value(b, "resource_id", "—"),
             "Bid (₹)": _value(b, "amount", "Invalid")}
            for b in bids
        ], use_container_width=True)
    else:
        st.caption("No bids recorded for this round.")
    if outcomes:
        st.subheader("Auction Outcomes")
        for result in outcomes:
            rid = _value(result, "resource_id", "—")
            winner = _value(result, "winner_id")
            amount = _value(result, "winning_bid", 0.0)
            amounts = bids_by_resource.get(str(rid), [])
            tied = _value(result, "tied", False) or (
                bool(amounts) and amounts.count(max(amounts)) > 1
            )
            if winner is None:
                st.info(f"{rid}: no valid bidder")
            else:
                st.success(f"**{rid}**: **{winner}** wins and pays ₹{amount:,.2f}")
            if tied:
                st.warning(f"Tie resolved for {rid}.")
    if invalid:
        st.subheader("Rejected Bids")
        st.warning("Malformed, wrong-resource, duplicate, or over-budget bids cannot win.")
        st.json([repr(b) for b in invalid])

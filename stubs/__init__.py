"""
stubs/__init__.py
=================
TEMPORARY MOCK / STUB AGENTS FOR ROLE B & ROLE C
These stand in for Role B (AuctioneerAgent) and Role C (DisruptionAgent, Baseline)
until their official implementations are merged into the main repository.
"""

from stubs.auctioneer_agent import AuctioneerAgent
from stubs.disruption_agent import DisruptionAgent
from stubs.baseline import compute_hungarian_baseline
from stubs.demo_panels import render_auction_panel, render_metrics_panel

__all__ = [
    "AuctioneerAgent",
    "DisruptionAgent",
    "compute_hungarian_baseline",
    "render_auction_panel",
    "render_metrics_panel",
]

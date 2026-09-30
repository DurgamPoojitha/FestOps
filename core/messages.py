"""
core/messages.py
================
SHARED TEAM CONTRACT — Do NOT modify field names without group agreement.

These dataclasses define the message types passed between agents:
  - Bid         : a committee's offer for one resource
  - AuctionResult : what the auctioneer returns after one resource's auction
  - DisruptionEvent : what Role C's DisruptionAgent emits when something breaks

All roles depend on this file.  Change only with everyone's consent.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Bid:
    """
    A single bid submitted by a committee for a resource.

    Fields
    ------
    committee_id : str
        The ID of the committee placing the bid.
    resource_id : str
        The ID of the resource being bid on.
    amount : float
        The monetary amount offered (non-negative).
    """

    committee_id: str
    resource_id: str
    amount: float


@dataclass
class AuctionResult:
    """
    The outcome of auctioning one resource (produced by Role B).

    Fields
    ------
    resource_id : str
        The resource that was auctioned.
    winner_id : str | None
        The committee that won, or None if no valid bids were placed.
    winning_bid : float
        The amount paid by the winner (0.0 if no winner).
    losers : list[str]
        Committee IDs that bid but did not win.
    """

    resource_id: str
    winner_id: str | None
    winning_bid: float
    losers: list[str]


@dataclass
class DisruptionEvent:
    """
    Signals that a resource has been disrupted mid-simulation (produced by Role C).

    Fields
    ------
    round_num : int
        The simulation round in which the disruption occurred.
    resource_id : str
        The resource that became unavailable.
    reason : str
        Human-readable cause, e.g. "equipment_failure" | "venue_unavailable" |
        "volunteer_dropout".
    """

    round_num: int
    resource_id: str
    reason: str

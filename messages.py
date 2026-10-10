"""Shared message contracts used by the FestOps agents."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Bid:
    committee_id: str
    resource_id: str
    amount: float


@dataclass
class AuctionResult:
    resource_id: str
    winner_id: str | None
    winning_bid: float
    losers: list[str]


@dataclass
class DisruptionEvent:
    round_num: int
    resource_id: str
    reason: str

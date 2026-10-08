"""Validation and winner selection for sealed first-price auctions."""

from __future__ import annotations

import math
from typing import Any, Callable

from core.messages import AuctionResult, Bid


def validate_bids(
    resource_id: str, bids: list[Any], committees: dict[str, Any]
) -> tuple[list[Bid], list[Any]]:
    """Return valid bids and rejected inputs; validates identity, amount and budget."""
    valid: list[Bid] = []
    invalid: list[Any] = []
    seen: set[str] = set()
    for bid in bids:
        try:
            committee_id = bid.committee_id
            bid_resource_id = bid.resource_id
            amount = float(bid.amount)
            committee = committees.get(committee_id)
            budget = float(committee.remaining_budget) if committee is not None else -1
            good = (
                isinstance(committee_id, str) and bool(committee_id)
                and bid_resource_id == resource_id and committee is not None
                and math.isfinite(amount) and amount > 0
                and amount <= budget and committee_id not in seen
            )
        except (AttributeError, TypeError, ValueError, OverflowError):
            good = False
        if not good:
            invalid.append(bid)
            continue
        seen.add(committee_id)
        valid.append(Bid(committee_id, resource_id, amount))
    return valid, invalid


def resolve_first_price(
    resource_id: str,
    bids: list[Bid],
    choose_tie: Callable[[list[Bid]], Bid],
) -> tuple[AuctionResult, bool]:
    """Select highest bid; ties use the injected chooser. Settlement is simulator-owned."""
    if not bids:
        return AuctionResult(resource_id, None, 0.0, []), False
    high = max(b.amount for b in bids)
    tied = [b for b in bids if b.amount == high]
    winner = choose_tie(tied) if len(tied) > 1 else tied[0]
    losers = [b.committee_id for b in bids if b.committee_id != winner.committee_id]
    return AuctionResult(resource_id, winner.committee_id, winner.amount, losers), len(tied) > 1

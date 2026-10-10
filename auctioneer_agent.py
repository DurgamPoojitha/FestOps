"""Auctioneer for sealed first-price allocation of campus resources."""

from __future__ import annotations

import logging
import random
from typing import Any, Callable

from core.auction import resolve_first_price, validate_bids
from core.messages import AuctionResult, Bid

logger = logging.getLogger(__name__)


def _resource_id(resource: Any) -> str:
    if isinstance(resource, dict):
        return str(resource["id"])
    return str(getattr(resource, "id", resource))


class AuctioneerAgent:
    """Resolves resource auctions; the simulator settles winners exactly once."""

    def __init__(
        self,
        rng: random.Random | None = None,
        tie_breaker: Callable[[list[Bid]], Bid] | None = None,
    ) -> None:
        self._rng = rng if rng is not None else random.Random()
        self._tie_breaker = tie_breaker
        self.last_round_results: list[AuctionResult] = []
        self.last_round_bids: list[Bid] = []
        self.last_invalid_bids: list[Any] = []

    def _choose_tie(self, bids: list[Bid]) -> Bid:
        if self._tie_breaker is not None:
            return self._tie_breaker(list(bids))
        return self._rng.choice(bids)

    def collect_bids(
        self, resource_id: str, bids: list[Bid], committees: list[Any] | None = None
    ) -> AuctionResult:
        """Validate submitted bids and resolve the auction without charging budgets.

        The established simulator API calls ``winner.allocate_resource`` once
        after receiving results, so charging here would double deduct.
        """
        committee_map = {str(c.id): c for c in (committees or [])}
        # Direct resolution remains useful to callers without a committee context;
        # in that case the provided bidders are still checked for shape and amount.
        if committees is None:
            committee_map = {
                str(b.committee_id): _BudgetView(float("inf"))
                for b in bids if isinstance(b, Bid) and isinstance(b.committee_id, str)
            }
        valid, invalid = validate_bids(resource_id, bids, committee_map)
        self.last_invalid_bids = invalid
        for bid in invalid:
            logger.warning("Rejected invalid bid for %s: %r", resource_id, bid)
        result, tied = resolve_first_price(resource_id, valid, self._choose_tie)
        if tied:
            logger.info("Tie at %.2f for resource %s; selected %s", result.winning_bid, resource_id, result.winner_id)
        return result

    def run_round(self, contested_resources: list[Any], committees: list[Any]) -> list[AuctionResult]:
        results: list[AuctionResult] = []
        all_bids: list[Bid] = []
        committee_map = {str(c.id): c for c in committees}
        invalid: list[Any] = []
        for resource in contested_resources:
            rid = _resource_id(resource)
            bids: list[Bid] = []
            for committee in committees:
                if (rid in getattr(committee, "wanted_resources", [])
                        and rid not in getattr(committee, "allocated_resources", [])):
                    try:
                        bid = committee.generate_bid({"id": rid})
                    except Exception as exc:
                        logger.warning("Could not generate bid for %s: %s", getattr(committee, "id", "?"), exc)
                        continue
                    bids.append(bid)
            valid, rejected = validate_bids(rid, bids, committee_map)
            invalid.extend(rejected)
            all_bids.extend(valid)
            result, tied = resolve_first_price(rid, valid, self._choose_tie)
            if tied:
                logger.info("Tie at %.2f for resource %s; selected %s", result.winning_bid, rid, result.winner_id)
            results.append(result)
        self.last_round_results = results
        self.last_round_bids = all_bids
        self.last_invalid_bids = invalid
        for bid in invalid:
            logger.warning("Rejected invalid bid: %r", bid)
        return results


class _BudgetView:
    def __init__(self, remaining_budget: float) -> None:
        self.remaining_budget = remaining_budget

"""
stubs/auctioneer_agent.py
=========================
TEMPORARY STUB — Standing in for Role B's `agents/auctioneer_agent.py`
This mock implementation allows Role D (Simulator & Demo) to build and run
end-to-end without waiting for Role B's branch to merge.

SWAP NOTICE:
Once Role B's code lands, replace imports of this class with:
    from agents.auctioneer_agent import AuctioneerAgent
"""

from __future__ import annotations

import random
from typing import Any

from core.messages import AuctionResult, Bid


class AuctioneerAgent:
    """
    Mock AuctioneerAgent standing in for Role B.

    Orchestrates sealed-bid auctions for contested resources.
    Selects the winning committee based on highest bid (with highest remaining
    budget as tiebreaker).
    """

    def __init__(self, rng: random.Random | None = None) -> None:
        self._rng: random.Random = rng if rng is not None else random.Random()
        self.last_round_results: list[AuctionResult] = []
        self.last_round_bids: list[Bid] = []

    def collect_bids(self, resource_id: str, bids: list[Bid]) -> AuctionResult:
        """
        Evaluate sealed bids for a single resource and pick the winner.

        Parameters
        ----------
        resource_id : str
            The identifier of the resource being auctioned.
        bids : list[Bid]
            Bids submitted by committees for this resource.

        Returns
        -------
        AuctionResult
            Outcome containing winner, winning bid, and losers.
        """
        if not bids:
            return AuctionResult(
                resource_id=resource_id,
                winner_id=None,
                winning_bid=0.0,
                losers=[],
            )

        # Shuffle bids first for fair tiebreaking, then sort descending by amount
        shuffled = list(bids)
        self._rng.shuffle(shuffled)
        sorted_bids = sorted(shuffled, key=lambda b: b.amount, reverse=True)

        winner_bid = sorted_bids[0]
        # Only declare a winner if the winning bid is > 0 (or valid)
        if winner_bid.amount > 0:
            winner_id = winner_bid.committee_id
            winning_bid = winner_bid.amount
            losers = [b.committee_id for b in sorted_bids if b.committee_id != winner_id]
        else:
            # If all bids were 0, award to first or declare no winner
            winner_id = winner_bid.committee_id
            winning_bid = 0.0
            losers = [b.committee_id for b in sorted_bids if b.committee_id != winner_id]

        return AuctionResult(
            resource_id=resource_id,
            winner_id=winner_id,
            winning_bid=winning_bid,
            losers=losers,
        )

    def run_round(
        self,
        contested_resources: list[str | dict | Any],
        committees: list[Any],
    ) -> list[AuctionResult]:
        """
        Orchestrate auctions for all contested resources in a round.

        Parameters
        ----------
        contested_resources : list[str | dict | Any]
            List of resource IDs or resource dicts contested this round.
        committees : list[CommitteeAgent]
            List of active committee agents.

        Returns
        -------
        list[AuctionResult]
            List of auction results, one per contested resource.
        """
        results: list[AuctionResult] = []
        all_bids: list[Bid] = []

        for resource in contested_resources:
            resource_id = resource["id"] if isinstance(resource, dict) else str(getattr(resource, "id", resource))

            # Gather bids from all committees that want this resource
            resource_bids: list[Bid] = []
            for committee in committees:
                # Check if committee wants this resource and doesn't already have it
                wanted = getattr(committee, "wanted_resources", [])
                allocated = getattr(committee, "allocated_resources", [])
                if resource_id in wanted and resource_id not in allocated:
                    bid = committee.generate_bid({"id": resource_id})
                    resource_bids.append(bid)
                    all_bids.append(bid)

            result = self.collect_bids(resource_id, resource_bids)
            results.append(result)

        self.last_round_results = results
        self.last_round_bids = all_bids
        return results

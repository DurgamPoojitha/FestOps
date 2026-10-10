import random

from agents.auctioneer_agent import AuctioneerAgent
from core.messages import Bid


class Committee:
    def __init__(self, cid, budget, amount=None):
        self.id = cid
        self.remaining_budget = budget
        self.wanted_resources = ["hall"]
        self.allocated_resources = []
        self.amount = amount

    def generate_bid(self, resource):
        return Bid(self.id, resource["id"], self.amount)

    def allocate_resource(self, resource_id, cost):
        self.remaining_budget = max(0.0, self.remaining_budget - cost)
        self.allocated_resources.append(resource_id)


def test_highest_valid_bid_wins_and_pays_bid_once_via_simulator_contract():
    low, high = Committee("low", 100, 20), Committee("high", 70, 40)
    auction = AuctioneerAgent()
    result = auction.run_round(["hall"], [low, high])[0]
    assert (result.winner_id, result.winning_bid) == ("high", 40)
    # The simulator applies the result through the committee's established API.
    next(c for c in [low, high] if c.id == result.winner_id).allocate_resource("hall", result.winning_bid)
    assert high.remaining_budget == 30


def test_tie_is_seeded_and_does_not_crash():
    committees = [Committee("a", 50, 25), Committee("b", 50, 25)]
    one = AuctioneerAgent(rng=random.Random(9)).run_round(["hall"], committees)[0]
    two = AuctioneerAgent(rng=random.Random(9)).run_round(["hall"], committees)[0]
    assert one.winner_id == two.winner_id
    assert one.winner_id in {"a", "b"}


def test_losers_pay_nothing():
    a, b = Committee("a", 100, 30), Committee("b", 100, 20)
    result = AuctioneerAgent().run_round(["hall"], [a, b])[0]
    for committee in [a, b]:
        if committee.id == result.winner_id:
            committee.allocate_resource("hall", result.winning_bid)
    assert a.remaining_budget == 70
    assert b.remaining_budget == 100


def test_budgets_never_negative_across_repeated_auctions():
    c = Committee("c", 10, 6)
    auction = AuctioneerAgent(rng=random.Random(2))
    for rid in ["hall", "second_hall"]:
        c.wanted_resources = [rid]
        result = auction.run_round([rid], [c])[0]
        if result.winner_id:
            c.allocate_resource(rid, result.winning_bid)
        assert c.remaining_budget >= 0
    assert c.remaining_budget >= 0


def test_invalid_wrong_resource_and_over_budget_bids_cannot_win():
    poor, rich = Committee("poor", 5), Committee("rich", 100)
    auction = AuctioneerAgent()
    result = auction.collect_bids("hall", [
        Bid("poor", "hall", 50),
        Bid("rich", "other", 99),
        Bid("rich", "hall", 10),
    ], [poor, rich])
    assert result.winner_id == "rich"
    assert result.winning_bid == 10
    assert len(auction.last_invalid_bids) == 2

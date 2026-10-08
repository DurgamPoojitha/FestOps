"""
core/simulator.py
=================
Role D — Discrete-Round Multi-Agent Simulation Engine for Fest Ops

Orchestrates the decentralized sealed-bid auction environment:
1. Detects contested vs uncontested resources among committee agents.
2. Calls the AuctioneerAgent (Role B) to resolve contested allocations.
3. Applies AuctionResults (allocates resources, deducts budgets, handles loser fallbacks).
4. Invokes the DisruptionAgent (Role C) to simulate dynamic real-world shocks.
5. On disruption, frees invalidated resources and requeues committees.
6. Records comprehensive round metrics (efficiency, Jain's fairness, utilization, recovery).

Agnostic to agent internal strategies — interacts strictly through public interfaces.
"""

from __future__ import annotations

from collections import defaultdict
import inspect
import random
from typing import Any, Sequence

import pandas as pd

from agents.committee_agent import CommitteeAgent
from core.messages import AuctionResult, Bid, DisruptionEvent
from core.metrics import (
    allocation_efficiency,
    fairness_index,
    recovery_time,
    resource_utilization,
)
from core.baseline import compute_hungarian_baseline


class Simulator:
    """
    Decentralized discrete-round simulation engine.

    Parameters
    ----------
    committees : list[CommitteeAgent]
        List of self-interested college fest committee agents.
    resources : list[dict | str | Any]
        List of available resources (venues, equipment, volunteer pools).
    auctioneer : Any
        AuctioneerAgent implementing `run_round(contested_resources, committees)`.
    disruption_agent : Any
        DisruptionAgent implementing `maybe_trigger(round_num)` and `force_trigger(resource_id)`.
    seed : int | None
        Seed for reproducibility.
    """

    def __init__(
        self,
        committees: list[CommitteeAgent],
        resources: list[dict | str | Any],
        auctioneer: Any,
        disruption_agent: Any,
        seed: int | None = None,
    ) -> None:
        self.committees: list[CommitteeAgent] = list(committees)
        self.committee_map: dict[str, CommitteeAgent] = {c.id: c for c in self.committees}

        # Normalize resources into a clean list of dicts with 'id'
        self.resources: list[dict[str, Any]] = []
        self.resource_ids: list[str] = []
        for r in resources:
            if isinstance(r, dict):
                self.resources.append(dict(r))
                self.resource_ids.append(r["id"])
            elif hasattr(r, "id"):
                self.resources.append({"id": r.id, "type": getattr(r, "type", "generic"), "capacity": getattr(r, "capacity", 1)})
                self.resource_ids.append(r.id)
            else:
                self.resources.append({"id": str(r), "type": "generic", "capacity": 1})
                self.resource_ids.append(str(r))

        self.auctioneer: Any = auctioneer
        self.disruption_agent: Any = disruption_agent
        self._rng: random.Random = random.Random(seed) if seed is not None else random.Random()

        # Simulation state tracking
        self.round_num: int = 0
        self.events: list[dict[str, Any]] = []
        self.disruptions_log: list[dict[str, Any]] = []
        self.disrupted_resources: set[str] = set()

        self.current_round_bids: list[dict[str, Any]] = []
        self.current_round_results: list[AuctionResult] = []

        # Calculate theoretical centralized maximum utility for efficiency baseline
        self.max_utility, self.optimal_assignment = compute_hungarian_baseline(
            self.committees, self.resources
        )
        if self.max_utility <= 0:
            # Fallback: estimate from sum of top desired resource valuation per committee
            self.max_utility = sum(
                max([c.compute_valuation({"id": r}) for r in c.wanted_resources] or [0.0])
                for c in self.committees
            )
            self.max_utility = max(self.max_utility, 1.0)

        # Logging dataframe
        self.history: list[dict[str, Any]] = []
        self.log: pd.DataFrame = pd.DataFrame()

    # -----------------------------------------------------------------------
    # Core Round Step
    # -----------------------------------------------------------------------

    def step(self) -> dict[str, Any]:
        """
        Advance the simulation by exactly one round.

        Returns
        -------
        dict[str, Any]
            The full state dictionary after this round completes.
        """
        self.round_num += 1
        self.current_round_bids.clear()
        self.current_round_results.clear()

        # 1. Identify currently unallocated resources
        currently_allocated: set[str] = {
            res for c in self.committees for res in c.allocated_resources
        }
        available_resources = [r for r in self.resource_ids if r not in currently_allocated]

        # 2. Detect resource demand from committees
        # Map: resource_id -> list of committees that want it and do not hold it
        demand: dict[str, list[CommitteeAgent]] = defaultdict(list)
        for c in self.committees:
            for wanted_res in c.wanted_resources:
                if wanted_res in available_resources and wanted_res not in c.allocated_resources:
                    demand[wanted_res].append(c)

        contested_resources: list[str] = [
            res for res, wanting in demand.items() if len(wanting) > 1
        ]
        uncontested_resources: list[str] = [
            res for res, wanting in demand.items() if len(wanting) == 1
        ]

        # 3. Process uncontested resources (sole bidder automatically wins)
        for res_id in uncontested_resources:
            sole_committee = demand[res_id][0]
            bid = sole_committee.generate_bid({"id": res_id})
            self.current_round_bids.append({
                "committee_id": bid.committee_id,
                "resource_id": bid.resource_id,
                "amount": bid.amount,
            })

            # Award resource to sole bidder
            sole_committee.allocate_resource(res_id, bid.amount)
            is_recovery = res_id in self.disrupted_resources
            event_type = "reallocated" if is_recovery else "allocated"

            self.events.append({
                "round": self.round_num,
                "event": event_type,
                "resource_id": res_id,
                "committee_id": sole_committee.id,
            })

            result = AuctionResult(
                resource_id=res_id,
                winner_id=sole_committee.id,
                winning_bid=bid.amount,
                losers=[],
            )
            self.current_round_results.append(result)

        # 4. Process contested resources through the AuctioneerAgent (Role B)
        if contested_resources:
            auction_results = self.auctioneer.run_round(contested_resources, self.committees)
            self.current_round_results.extend(auction_results)

            # Record bids placed during this round
            for res_id in contested_resources:
                for c in demand[res_id]:
                    # Estimate or retrieve submitted bid for display
                    b_amount = c.compute_valuation({"id": res_id})
                    self.current_round_bids.append({
                        "committee_id": c.id,
                        "resource_id": res_id,
                        "amount": b_amount,
                    })

            # 5. Apply auction outcomes
            for result in auction_results:
                # Refresh available pool
                cur_alloc = {res for c in self.committees for res in c.allocated_resources}
                cur_avail = [{"id": r} for r in self.resource_ids if r not in cur_alloc]

                # (a) Handle winner
                if result.winner_id is not None and result.winner_id in self.committee_map:
                    winner = self.committee_map[result.winner_id]
                    winner.allocate_resource(result.resource_id, result.winning_bid)

                    is_recovery = result.resource_id in self.disrupted_resources
                    event_type = "reallocated" if is_recovery else "allocated"
                    self.events.append({
                        "round": self.round_num,
                        "event": event_type,
                        "resource_id": result.resource_id,
                        "committee_id": winner.id,
                    })

                # (b) Handle losers
                for loser_id in result.losers:
                    if loser_id in self.committee_map:
                        loser = self.committee_map[loser_id]
                        loss_outcome = loser.on_lost_auction(
                            {"id": result.resource_id}, available_resources=cur_avail
                        )

                        if loss_outcome.get("status") == "substitute":
                            sub_id = loss_outcome.get("resource_id")
                            if sub_id:
                                # Fall back to substitute in wanted_resources
                                if result.resource_id in loser.wanted_resources:
                                    idx = loser.wanted_resources.index(result.resource_id)
                                    loser.wanted_resources[idx] = sub_id
                                elif sub_id not in loser.wanted_resources:
                                    loser.wanted_resources.append(sub_id)

                                self.events.append({
                                    "round": self.round_num,
                                    "event": "substitute_fallback",
                                    "resource_id": sub_id,
                                    "committee_id": loser.id,
                                })
                        else:
                            # Partial fulfillment — remove contested resource from wanted list
                            if result.resource_id in loser.wanted_resources:
                                loser.wanted_resources.remove(result.resource_id)

                            self.events.append({
                                "round": self.round_num,
                                "event": "partial_fulfillment",
                                "resource_id": result.resource_id,
                                "committee_id": loser.id,
                            })

        # 6. Check stochastic disruption via DisruptionAgent (Role C)
        active_awarded: list[str] = [
            res for c in self.committees for res in c.allocated_resources
        ]

        # Safely invoke maybe_trigger (supports both targetable_resources kwarg and plain round_num)
        disruption_event: DisruptionEvent | None = None
        if active_awarded:
            sig = inspect.signature(self.disruption_agent.maybe_trigger)
            if "targetable_resources" in sig.parameters:
                disruption_event = self.disruption_agent.maybe_trigger(
                    self.round_num, targetable_resources=active_awarded
                )
            else:
                disruption_event = self.disruption_agent.maybe_trigger(self.round_num)

        if disruption_event is not None:
            self._apply_disruption(disruption_event)

        # 7. Compute round metrics and update DataFrame log
        self._record_metrics_snapshot(disrupted_this_round=bool(disruption_event))

        return self.get_state()

    # -----------------------------------------------------------------------
    # Disruption Mechanics
    # -----------------------------------------------------------------------

    def _apply_disruption(self, event: DisruptionEvent) -> None:
        """
        Apply a disruption event: invalidate resource and requeue the affected committee.
        """
        res_id = event.resource_id
        # Find which committee currently holds this resource
        holder = next((c for c in self.committees if res_id in c.allocated_resources), None)

        if holder is not None:
            # Free the resource
            holder.allocated_resources.remove(res_id)

            # Requeue the affected committee so it re-competes or seeks substitutes
            if res_id not in holder.wanted_resources:
                holder.wanted_resources.append(res_id)

            self.disrupted_resources.add(res_id)

            disruption_record = {
                "round": self.round_num,
                "event": "disruption",
                "resource_id": res_id,
                "committee_id": holder.id,
                "reason": event.reason,
            }
            self.events.append(disruption_record)
            self.disruptions_log.append(disruption_record)

    def force_disruption(self, resource_id: str | None = None) -> DisruptionEvent:
        """
        Deterministically trigger a disruption event (for live demo button or tests).

        Parameters
        ----------
        resource_id : str | None
            Specific resource to disrupt. If None, targets a currently allocated resource.

        Returns
        -------
        DisruptionEvent
            The forced disruption event.
        """
        active_awarded = [res for c in self.committees for res in c.allocated_resources]

        # Call disruption agent's force_trigger
        sig = inspect.signature(self.disruption_agent.force_trigger)
        if "fallback_resources" in sig.parameters:
            event = self.disruption_agent.force_trigger(
                resource_id=resource_id,
                round_num=self.round_num,
                fallback_resources=active_awarded,
            )
        else:
            event = self.disruption_agent.force_trigger(resource_id=resource_id)

        self._apply_disruption(event)
        self._record_metrics_snapshot(disrupted_this_round=True)
        return event

    # -----------------------------------------------------------------------
    # Metrics Logging
    # -----------------------------------------------------------------------

    def _record_metrics_snapshot(self, disrupted_this_round: bool = False) -> None:
        """Calculate system metrics and append row to self.log DataFrame."""
        # 1. Obtained utility across all committees
        obtained_utility = sum(
            c.compute_valuation({"id": r}) for c in self.committees for r in c.allocated_resources
        )
        eff = allocation_efficiency(obtained_utility, self.max_utility)

        # 2. Per-committee utility for Jain's fairness index
        committee_utilities = [
            sum(c.compute_valuation({"id": r}) for r in c.allocated_resources)
            for c in self.committees
        ]
        fair = fairness_index(committee_utilities)

        # 3. Resource utilization
        allocated_unique = len({r for c in self.committees for r in c.allocated_resources})
        total_unique = len(self.resources)
        util = resource_utilization(allocated_unique, total_unique)

        # 4. Total remaining budget
        total_budget_left = sum(c.remaining_budget for c in self.committees)

        row = {
            "round": self.round_num,
            "obtained_utility": round(obtained_utility, 2),
            "max_utility": round(self.max_utility, 2),
            "allocation_efficiency": round(eff, 4),
            "fairness_index": round(fair, 4),
            "resource_utilization": round(util, 4),
            "allocated_count": allocated_unique,
            "total_resources": total_unique,
            "remaining_budget_total": round(total_budget_left, 2),
            "disruption_active": disrupted_this_round,
        }
        self.history.append(row)
        self.log = pd.DataFrame(self.history)

    # -----------------------------------------------------------------------
    # Execution Helpers & State Export
    # -----------------------------------------------------------------------

    def run(self, n_rounds: int) -> pd.DataFrame:
        """
        Execute simulation for N rounds headlessly.

        Parameters
        ----------
        n_rounds : int
            Number of rounds to execute.

        Returns
        -------
        pd.DataFrame
            Complete simulation history log.
        """
        for _ in range(n_rounds):
            self.step()
        return self.log

    def get_state(self) -> dict[str, Any]:
        """
        Export the current simulation state dictionary consumed by all demo panels.

        Returns
        -------
        dict[str, Any]
            Complete simulation snapshot.
        """
        latest_metrics = self.history[-1] if self.history else {
            "allocation_efficiency": 0.0,
            "fairness_index": 1.0,
            "resource_utilization": 0.0,
            "obtained_utility": 0.0,
            "max_utility": self.max_utility,
        }

        return {
            "round": self.round_num,
            "committees": [c.get_state() for c in self.committees],
            "resources": list(self.resources),
            "bids": list(self.current_round_bids),
            "auction_results": list(self.current_round_results),
            "disruptions": list(self.disruptions_log),
            "events": list(self.events),
            "metrics": latest_metrics,
            "log": self.log,
        }

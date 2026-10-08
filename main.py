"""
main.py
=======
Role D — Headless CLI Runner for Fest Ops Multi-Agent Simulation

Usage:
    python main.py --scenario config/scenario_default.yaml
    python main.py --scenario config/scenario_disruption.yaml

Loads scenario parameters and Role A YAML configurations, initializes all agents
(real CommitteeAgents + stub Auctioneer/Disruption agents), runs discrete-round
simulation, and prints final performance metrics.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import random
import sys
from typing import Any
import yaml

from agents.committee_agent import CommitteeAgent
from core.metrics import (
    allocation_efficiency,
    fairness_index,
    recovery_time,
    resource_utilization,
)
from core.simulator import Simulator

# Real agent implementations
from agents.auctioneer_agent import AuctioneerAgent
from agents.disruption_agent import DisruptionAgent


def load_yaml(filepath: str | Path) -> dict[str, Any]:
    """Safely load and parse a YAML file."""
    path = Path(filepath)
    if not path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {filepath}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def build_simulation(scenario_path: str | Path) -> tuple[Simulator, dict[str, Any]]:
    """
    Construct the Simulator and agent graph from scenario and asset configs.

    Returns
    -------
    tuple[Simulator, dict[str, Any]]
        The initialized Simulator instance and scenario config dict.
    """
    scenario = load_yaml(scenario_path)

    project_root = Path(__file__).resolve().parent
    committees_file = project_root / scenario.get("committees_file", "config/committees.yaml")
    resources_file = project_root / scenario.get("resources_file", "config/resources.yaml")

    committees_raw = load_yaml(committees_file).get("committees", [])
    resources_raw = load_yaml(resources_file).get("resources", [])

    seed = scenario.get("seed", 42)
    rng = random.Random(seed)

    # 1. Build Role A real CommitteeAgents
    committees = [
        CommitteeAgent(
            committee_id=c["id"],
            budget=float(c["budget"]),
            priorities=dict(c["priorities"]),
            wanted_resources=list(c["wanted_resources"]),
            substitutes=dict(c.get("substitutes", {})),
            rng=random.Random(rng.randint(0, 100_000)),
        )
        for c in committees_raw
    ]

    # 2. Build Role B AuctioneerAgent (Stub)
    auctioneer = AuctioneerAgent(rng=random.Random(rng.randint(0, 100_000)))

    # 3. Build Role C DisruptionAgent (Stub)
    disruption_prob = float(scenario.get("disruption_probability", 0.0))
    disruption_agent = DisruptionAgent(
        probability=disruption_prob,
        rng=random.Random(rng.randint(0, 100_000)),
    )

    # 4. Assemble Role D Simulator
    sim = Simulator(
        committees=committees,
        resources=resources_raw,
        auctioneer=auctioneer,
        disruption_agent=disruption_agent,
        seed=seed,
    )

    return sim, scenario


def print_simulation_report(sim: Simulator, scenario: dict[str, Any]) -> None:
    """Print an attractive and comprehensive terminal summary report."""
    print("\n" + "=" * 76)
    print("  FEST OPS -- MULTI-AGENT RESOURCE ALLOCATION SIMULATION")
    print("  23CSE401 Foundations of AI Case Study")
    print("=" * 76)
    print(f"Scenario Name:        {scenario.get('name', 'Custom')}")
    print(f"Description:          {scenario.get('description', 'N/A')}")
    print(f"Rounds Executed:      {sim.round_num}")
    print(f"Disruption Rate:      {scenario.get('disruption_probability', 0.0)}")
    print("-" * 76)

    # Calculate final metrics using Role A's metrics.py
    obtained_utility = sum(
        c.compute_valuation({"id": r}) for c in sim.committees for r in c.allocated_resources
    )
    final_efficiency = allocation_efficiency(obtained_utility, sim.max_utility)

    committee_utilities = [
        sum(c.compute_valuation({"id": r}) for r in c.allocated_resources)
        for c in sim.committees
    ]
    final_fairness = fairness_index(committee_utilities)

    allocated_unique = len({r for c in sim.committees for r in c.allocated_resources})
    total_resources = len(sim.resources)
    final_utilization = resource_utilization(allocated_unique, total_resources)

    # Committee Breakdown Table
    print("\n[COMMITTEE ALLOCATION BREAKDOWN]:")
    print(f"{'Committee':<20} | {'Budget (Spent/Total)':<20} | {'Won Resources':<20} | {'Partial'}")
    print("-" * 76)
    for c in sim.committees:
        spent = c.budget - c.remaining_budget
        budget_str = f"Rs.{spent:.0f} / Rs.{c.budget:.0f}"
        alloc_str = ", ".join(c.allocated_resources) if c.allocated_resources else "-"
        partial_str = ", ".join(c.partial_fulfillment) if c.partial_fulfillment else "-"
        print(f"{c.id:<20} | {budget_str:<20} | {alloc_str:<20} | {partial_str}")

    # Disruption & Recovery Summary
    if sim.disruptions_log:
        print("\n[DISRUPTIONS & RECOVERY TRACKING]:")
        print(f"{'Round':<6} | {'Resource':<25} | {'Victim':<18} | {'Recovery Time'}")
        print("-" * 76)
        for d in sim.disruptions_log:
            rec_time = recovery_time(
                sim.events,
                disruption_round=d["round"],
                resource_id=d["resource_id"],
                committee_id=d["committee_id"],
            )
            rec_str = f"{rec_time} round(s)" if rec_time is not None else "Pending / Unrecovered"
            print(f"{d['round']:<6} | {d['resource_id']:<25} | {d['committee_id']:<18} | {rec_str}")
    else:
        print("\n[DISRUPTIONS]: No disruptions occurred in this run.")

    # KPI Summary Box
    print("\n" + "=" * 76)
    print("FINAL SYSTEM KEY PERFORMANCE INDICATORS (KPIs):")
    print("-" * 76)
    print(f" * Allocation Efficiency:    {final_efficiency * 100:.2f}%  (Decentralized: {obtained_utility:.1f} / Hungarian Optimal: {sim.max_utility:.1f})")
    print(f" * Jain's Fairness Index:    {final_fairness:.4f}   (1.0 = Perfectly Fair across all committees)")
    print(f" * Resource Utilization:     {final_utilization * 100:.2f}%  ({allocated_unique} of {total_resources} unique resources utilized)")
    print("=" * 76 + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fest Ops Multi-Agent Decentralized Auction Simulation CLI"
    )
    parser.add_argument(
        "--scenario",
        type=str,
        default="config/scenario_default.yaml",
        help="Path to scenario YAML configuration file",
    )
    parser.add_argument(
        "--rounds",
        type=int,
        default=None,
        help="Override number of simulation rounds to execute",
    )
    args = parser.parse_args()

    scenario_file = Path(args.scenario)
    if not scenario_file.exists():
        print(f"Error: Scenario file '{args.scenario}' not found.", file=sys.stderr)
        sys.exit(1)

    sim, scenario = build_simulation(scenario_file)
    n_rounds = args.rounds or scenario.get("rounds", 10)

    print(f"Starting Fest Ops simulation for {n_rounds} rounds using scenario: {args.scenario}...")
    sim.run(n_rounds)
    print_simulation_report(sim, scenario)


if __name__ == "__main__":
    main()

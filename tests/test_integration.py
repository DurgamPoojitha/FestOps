"""
tests/test_integration.py
==========================
Role D — End-to-End Integration Test Suite for Fest Ops

Tests the integration of:
- Real Role A: CommitteeAgent, metrics (allocation_efficiency, fairness_index, etc.)
- Stub Role B: AuctioneerAgent (run_round, collect_bids)
- Stub Role C: DisruptionAgent, Hungarian baseline
- Real Role D: Simulator discrete-round engine and state pipeline
"""

from __future__ import annotations

import os
from pathlib import Path
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest

from agents.committee_agent import CommitteeAgent
from core.messages import AuctionResult, DisruptionEvent
from core.metrics import (
    allocation_efficiency,
    fairness_index,
    resource_utilization,
)
from core.simulator import Simulator
from main import build_simulation


class TestFestOpsIntegration:
    """Integration test suite for Role D Simulator and agent pipeline."""

    def test_end_to_end_default_scenario(self):
        """
        Primary requirement: build scenario with real A + stub B/C, run 10 rounds,
        assert no exception, and verify allocation efficiency is a valid number in [0, 1].
        """
        scenario_file = PROJECT_ROOT / "config" / "scenario_default.yaml"
        assert scenario_file.exists(), f"Scenario file missing: {scenario_file}"

        sim, scenario = build_simulation(scenario_file)
        assert len(sim.committees) == 5, "Expected 5 committees from committees.yaml"
        assert len(sim.resources) == 6, "Expected 6 resources from resources.yaml"

        # Execute 10 rounds
        log_df = sim.run(10)

        # Assertions on execution
        assert sim.round_num == 10
        assert len(log_df) == 10
        assert not log_df.empty

        # Assert final efficiency is a valid float between 0.0 and 1.0
        final_efficiency = log_df["allocation_efficiency"].iloc[-1]
        assert isinstance(final_efficiency, (int, float))
        assert 0.0 <= final_efficiency <= 1.0, f"Efficiency {final_efficiency} out of bounds [0, 1]"

        # Assert Jain's fairness index is valid in (0, 1]
        final_fairness = log_df["fairness_index"].iloc[-1]
        assert 0.0 < final_fairness <= 1.0, f"Fairness {final_fairness} out of bounds (0, 1]"

        # Assert resource utilization is valid in [0, 1]
        final_util = log_df["resource_utilization"].iloc[-1]
        assert 0.0 <= final_util <= 1.0

        # In default scenario with 0 disruption probability, no disruptions should occur
        assert len(sim.disruptions_log) == 0

    def test_end_to_end_disruption_scenario(self):
        """
        Run disruption scenario (0.35 probability) for 15 rounds.
        Assert simulation executes cleanly and handles disruption events.
        """
        scenario_file = PROJECT_ROOT / "config" / "scenario_disruption.yaml"
        sim, scenario = build_simulation(scenario_file)

        log_df = sim.run(15)

        assert sim.round_num == 15
        assert len(log_df) == 15

        final_efficiency = log_df["allocation_efficiency"].iloc[-1]
        assert 0.0 <= final_efficiency <= 1.0

        # At 0.35 probability over 15 rounds, disruptions are expected
        # (Though stochastic, disruptions_log tracks any that occurred)
        for d in sim.disruptions_log:
            assert "round" in d
            assert "resource_id" in d
            assert "committee_id" in d
            assert "reason" in d

    def test_manual_force_disruption_frees_and_requeues(self):
        """
        Verify Simulator.force_disruption() frees the awarded resource
        and requeues the affected committee into wanted_resources.
        """
        scenario_file = PROJECT_ROOT / "config" / "scenario_default.yaml"
        sim, _ = build_simulation(scenario_file)

        # Step 2 rounds to allocate resources
        sim.step()
        sim.step()

        # Find any currently awarded resource and its holder
        holder = next((c for c in sim.committees if len(c.allocated_resources) > 0), None)
        assert holder is not None, "At least one committee should hold a resource by round 2"

        target_res = holder.allocated_resources[0]
        assert target_res in holder.allocated_resources

        # Trigger forced disruption
        disruption_event = sim.force_disruption(resource_id=target_res)

        assert isinstance(disruption_event, DisruptionEvent)
        assert disruption_event.resource_id == target_res

        # Resource must be freed from holder's allocated list
        assert target_res not in holder.allocated_resources

        # Committee must be requeued (resource added back to wanted list)
        assert target_res in holder.wanted_resources

        # Next step: committee should attempt to re-acquire or re-negotiate
        sim.step()
        assert sim.round_num == 3

    def test_simulation_state_dictionary_structure(self):
        """
        Verify Simulator.get_state() contains all contracts needed by Streamlit panels.
        """
        scenario_file = PROJECT_ROOT / "config" / "scenario_default.yaml"
        sim, _ = build_simulation(scenario_file)
        sim.step()

        state = sim.get_state()

        required_keys = {
            "round",
            "committees",
            "resources",
            "bids",
            "auction_results",
            "disruptions",
            "events",
            "metrics",
            "log",
        }
        for key in required_keys:
            assert key in state, f"Missing required state key: '{key}'"

        # Verify committee items match CommitteeAgent.get_state()
        for comm in state["committees"]:
            assert "id" in comm
            assert "budget" in comm
            assert "remaining_budget" in comm
            assert "allocated_resources" in comm

        # Verify metrics block
        assert "allocation_efficiency" in state["metrics"]
        assert "fairness_index" in state["metrics"]
        assert "resource_utilization" in state["metrics"]

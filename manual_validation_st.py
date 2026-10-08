import sys
from demo.committee_panel import render_committee_panel

try:
    render_committee_panel({})
    print("Empty state OK")
except Exception as e:
    print(f"Empty state failed: {e}")

try:
    render_committee_panel({"committees": [], "bids": [], "round": 1})
    print("Minimal state OK")
except Exception as e:
    print(f"Minimal state failed: {e}")

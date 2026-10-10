# Slide 3 — PEAS: Actuators & Sensors

**Actuators**
- Submit a sealed bid; revise a bid before close; withdraw a bid.
- Request a re-auction after a disruption; accept an award.

**Sensors**
- Own remaining budget and resource utility.
- Resource availability and auction results.
- Disruption notices affecting an awarded or requested resource.

**Speaker notes:** A committee observes its own budget and valuations plus the shared availability and outcome signals exposed by the environment. Its actions are limited to bids and responses supported by the round protocol. A losing committee’s substitute or partial-fulfilment response belongs to its committee logic, not the auctioneer.

# Slide 4 — Self-Interested Bidding, Cooperative Mechanism

> “Agents are self-interested/non-cooperative in their bidding (each maximizes its own utility), operating inside a cooperatively-designed mechanism (the auction protocol) whose purpose is to convert individually rational bidding into a globally efficient outcome.”

- Sealed first-price rule: the highest valid bid wins and pays its bid; losers pay nothing.
- The mechanism supplies a shared, auditable rule for competing over scarce campus resources.
- **Novelty, scoped carefully:** to the best of our search, our contribution is applying auction coordination and disruption re-negotiation to fest/campus logistics. Auction mechanisms themselves are established theory.

**Speaker notes:** Distinguish the strategic agents from the protocol that coordinates them. This is not a claim that auctions are new. The case study adapts established mechanism-design ideas to a practical campus setting and examines how committees recover when disruptions change resource availability.

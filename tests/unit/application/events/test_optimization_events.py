"""Unit tests for RuleEngagedEvent."""

import unittest
import uuid

from edge_mining.domain.optimization_unit.events import RuleEngagedEvent
from edge_mining.domain.common import DomainEvent, EntityId
from edge_mining.domain.policy.common import MiningDecision


class TestRuleEngagedEvent(unittest.TestCase):
    """Test cases for RuleEngagedEvent."""

    def test_inherits_from_domain_event(self):
        event = RuleEngagedEvent()
        self.assertIsInstance(event, DomainEvent)

    def test_creation_with_properties(self):
        unit_id = EntityId(uuid.uuid4())
        policy_id = EntityId(uuid.uuid4())
        miner_id = EntityId(uuid.uuid4())
        event = RuleEngagedEvent(
            optimization_unit_id=unit_id,
            optimization_unit_name="Unit 1",
            policy_id=policy_id,
            policy_name="Solar Policy",
            miner_id=miner_id,
            decision=MiningDecision.START_MINING,
            miner_status="OFF",
        )
        self.assertEqual(event.optimization_unit_id, unit_id)
        self.assertEqual(event.optimization_unit_name, "Unit 1")
        self.assertEqual(event.policy_id, policy_id)
        self.assertEqual(event.policy_name, "Solar Policy")
        self.assertEqual(event.miner_id, miner_id)
        self.assertEqual(event.decision, MiningDecision.START_MINING)
        self.assertEqual(event.miner_status, "OFF")

    def test_has_event_id_and_occurred_at(self):
        event = RuleEngagedEvent()
        self.assertIsNotNone(event.event_id)
        self.assertIsNotNone(event.occurred_at)

    def test_event_type_property(self):
        event = RuleEngagedEvent()
        self.assertEqual(event.event_type, "RuleEngagedEvent")

    def test_to_dict_includes_all_fields(self):
        unit_id = EntityId(uuid.uuid4())
        event = RuleEngagedEvent(
            optimization_unit_id=unit_id,
            optimization_unit_name="Unit 1",
            decision=MiningDecision.STOP_MINING,
            miner_status="ON",
        )
        result = event.to_dict()
        self.assertEqual(result["optimization_unit_name"], "Unit 1")
        self.assertEqual(result["event_type"], "RuleEngagedEvent")
        self.assertIn("event_id", result)
        self.assertIn("occurred_at", result)

    def test_defaults(self):
        event = RuleEngagedEvent()
        self.assertIsNone(event.optimization_unit_id)
        self.assertEqual(event.optimization_unit_name, "")
        self.assertIsNone(event.policy_id)
        self.assertEqual(event.policy_name, "")
        self.assertIsNone(event.miner_id)
        self.assertIsNone(event.decision)
        self.assertEqual(event.miner_status, "")


if __name__ == "__main__":
    unittest.main()

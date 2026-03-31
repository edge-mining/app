"""Unit tests for MinerStateChangedEvent."""

import unittest
import uuid

from edge_mining.application.events.miner_events import MinerStateChangedEvent
from edge_mining.domain.common import DomainEvent, EntityId
from edge_mining.domain.miner.common import MinerStatus


class TestMinerStateChangedEvent(unittest.TestCase):
    """Test cases for MinerStateChangedEvent."""

    def test_inherits_from_domain_event(self):
        event = MinerStateChangedEvent()
        self.assertIsInstance(event, DomainEvent)

    def test_creation_with_properties(self):
        miner_id = EntityId(uuid.uuid4())
        event = MinerStateChangedEvent(
            miner_id=miner_id,
            miner_name="Antminer S19",
            old_status=MinerStatus.OFF,
            new_status=MinerStatus.ON,
        )
        self.assertEqual(event.miner_id, miner_id)
        self.assertEqual(event.miner_name, "Antminer S19")
        self.assertEqual(event.old_status, MinerStatus.OFF)
        self.assertEqual(event.new_status, MinerStatus.ON)

    def test_has_event_id_and_occurred_at(self):
        event = MinerStateChangedEvent()
        self.assertIsNotNone(event.event_id)
        self.assertIsNotNone(event.occurred_at)

    def test_event_type_property(self):
        event = MinerStateChangedEvent()
        self.assertEqual(event.event_type, "MinerStateChangedEvent")

    def test_to_dict_includes_all_fields(self):
        miner_id = EntityId(uuid.uuid4())
        event = MinerStateChangedEvent(
            miner_id=miner_id,
            miner_name="Test Miner",
            old_status=MinerStatus.ON,
            new_status=MinerStatus.OFF,
        )
        result = event.to_dict()
        self.assertEqual(result["miner_name"], "Test Miner")
        self.assertEqual(result["event_type"], "MinerStateChangedEvent")
        self.assertIn("event_id", result)
        self.assertIn("occurred_at", result)

    def test_defaults(self):
        event = MinerStateChangedEvent()
        self.assertIsNone(event.miner_id)
        self.assertEqual(event.miner_name, "")
        self.assertIsNone(event.old_status)
        self.assertIsNone(event.new_status)


if __name__ == "__main__":
    unittest.main()

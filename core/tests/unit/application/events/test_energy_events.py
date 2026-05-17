"""Unit tests for EnergyStateSnapshotUpdatedEvent."""

import unittest
import uuid

from edge_mining.domain.energy.events import EnergyStateSnapshotUpdatedEvent
from edge_mining.domain.common import DomainEvent, EntityId


class TestEnergyStateSnapshotUpdatedEvent(unittest.TestCase):
    """Test cases for EnergyStateSnapshotUpdatedEvent."""

    def test_inherits_from_domain_event(self):
        event = EnergyStateSnapshotUpdatedEvent()
        self.assertIsInstance(event, DomainEvent)

    def test_creation_with_properties(self):
        unit_id = EntityId(uuid.uuid4())
        source_id = EntityId(uuid.uuid4())
        event = EnergyStateSnapshotUpdatedEvent(
            optimization_unit_id=unit_id,
            optimization_unit_name="Solar Unit",
            energy_source_id=source_id,
        )
        self.assertEqual(event.optimization_unit_id, unit_id)
        self.assertEqual(event.optimization_unit_name, "Solar Unit")
        self.assertEqual(event.energy_source_id, source_id)

    def test_has_event_id_and_occurred_at(self):
        event = EnergyStateSnapshotUpdatedEvent()
        self.assertIsNotNone(event.event_id)
        self.assertIsNotNone(event.occurred_at)

    def test_event_type_property(self):
        event = EnergyStateSnapshotUpdatedEvent()
        self.assertEqual(event.event_type, "EnergyStateSnapshotUpdatedEvent")

    def test_to_dict_includes_all_fields(self):
        event = EnergyStateSnapshotUpdatedEvent(
            optimization_unit_name="Unit 1",
        )
        result = event.to_dict()
        self.assertEqual(result["optimization_unit_name"], "Unit 1")
        self.assertEqual(result["event_type"], "EnergyStateSnapshotUpdatedEvent")
        self.assertIn("event_id", result)
        self.assertIn("occurred_at", result)

    def test_defaults(self):
        event = EnergyStateSnapshotUpdatedEvent()
        self.assertIsNone(event.optimization_unit_id)
        self.assertEqual(event.optimization_unit_name, "")
        self.assertIsNone(event.energy_source_id)
        self.assertIsNone(event.energy_state_snapshot)


if __name__ == "__main__":
    unittest.main()

"""Unit tests for DecisionalContextUpdatedEvent."""

import unittest
import uuid

from edge_mining.domain.policy.events import DecisionalContextUpdatedEvent
from edge_mining.domain.common import DomainEvent, EntityId
from edge_mining.domain.policy.value_objects import DecisionalContext


class TestDecisionalContextUpdatedEvent(unittest.TestCase):
    """Test cases for DecisionalContextUpdatedEvent."""

    def test_inherits_from_domain_event(self):
        event = DecisionalContextUpdatedEvent()
        self.assertIsInstance(event, DomainEvent)

    def test_creation_with_properties(self):
        unit_id = EntityId(uuid.uuid4())
        miner_id_1 = EntityId(uuid.uuid4())
        miner_id_2 = EntityId(uuid.uuid4())
        context = DecisionalContext(
            energy_source=None,
            energy_state=None,
            forecast=None,
            home_load=None,
            mining_performance=None,
        )
        event = DecisionalContextUpdatedEvent(
            optimization_unit_id=unit_id,
            optimization_unit_name="Solar Unit",
            context=context,
            target_miner_ids=[miner_id_1, miner_id_2],
        )
        self.assertEqual(event.optimization_unit_id, unit_id)
        self.assertEqual(event.optimization_unit_name, "Solar Unit")
        self.assertIs(event.context, context)
        self.assertEqual(event.target_miner_ids, [miner_id_1, miner_id_2])

    def test_has_event_id_and_occurred_at(self):
        event = DecisionalContextUpdatedEvent()
        self.assertIsNotNone(event.event_id)
        self.assertIsNotNone(event.occurred_at)

    def test_event_type_property(self):
        event = DecisionalContextUpdatedEvent()
        self.assertEqual(event.event_type, "DecisionalContextUpdatedEvent")

    def test_defaults(self):
        event = DecisionalContextUpdatedEvent()
        self.assertIsNone(event.optimization_unit_id)
        self.assertEqual(event.optimization_unit_name, "")
        self.assertIsNone(event.context)
        self.assertEqual(event.target_miner_ids, [])

    def test_target_miner_ids_default_is_independent(self):
        """Each instance should get its own list."""
        event1 = DecisionalContextUpdatedEvent()
        event2 = DecisionalContextUpdatedEvent()
        event1.target_miner_ids.append(EntityId(uuid.uuid4()))
        self.assertEqual(len(event2.target_miner_ids), 0)


if __name__ == "__main__":
    unittest.main()

"""Unit tests for ConfigurationUpdatedEvent."""

import unittest
import uuid

from edge_mining.application.events.configuration_events import ConfigurationUpdatedEvent, ConfigurationUpdatedEventType
from edge_mining.domain.common import DomainEvent, EntityId


class TestConfigurationUpdatedEvent(unittest.TestCase):
    """Test cases for ConfigurationUpdatedEvent."""

    def test_inherits_from_domain_event(self):
        event = ConfigurationUpdatedEvent()
        self.assertIsInstance(event, DomainEvent)

    def test_creation_with_properties(self):
        entity_id = EntityId(uuid.uuid4())
        event = ConfigurationUpdatedEvent(
            entity_type=ConfigurationUpdatedEventType.ENERGY_MONITOR,
            entity_id=entity_id,
            action="created",
        )
        self.assertEqual(event.entity_type, ConfigurationUpdatedEventType.ENERGY_MONITOR)
        self.assertEqual(event.entity_id, entity_id)
        self.assertEqual(event.action, "created")

    def test_has_event_id_and_occurred_at(self):
        event = ConfigurationUpdatedEvent()
        self.assertIsNotNone(event.event_id)
        self.assertIsNotNone(event.occurred_at)

    def test_event_type_property(self):
        event = ConfigurationUpdatedEvent()
        self.assertEqual(event.event_type, "ConfigurationUpdatedEvent")

    def test_to_dict_includes_all_fields(self):
        entity_id = EntityId(uuid.uuid4())
        event = ConfigurationUpdatedEvent(
            entity_type=ConfigurationUpdatedEventType.NOTIFIER,
            entity_id=entity_id,
            action="removed",
        )
        result = event.to_dict()
        self.assertEqual(result["entity_type"], ConfigurationUpdatedEventType.NOTIFIER)
        self.assertEqual(result["action"], "removed")
        self.assertEqual(result["event_type"], "ConfigurationUpdatedEvent")
        self.assertIn("event_id", result)
        self.assertIn("occurred_at", result)

    def test_defaults(self):
        event = ConfigurationUpdatedEvent()
        self.assertEqual(event.entity_type, ConfigurationUpdatedEventType.UNKNOWN)
        self.assertIsNone(event.entity_id)
        self.assertEqual(event.action, "")


if __name__ == "__main__":
    unittest.main()

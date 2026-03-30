"""Unit tests for DomainEvent base class."""

import unittest
from dataclasses import dataclass
from datetime import datetime, timezone

from edge_mining.domain.common import DomainEvent


@dataclass
class SampleEvent(DomainEvent):
    """Concrete event for testing."""

    name: str = ""


class TestDomainEvent(unittest.TestCase):
    """Test cases for DomainEvent base class."""

    def test_event_id_auto_generated(self):
        event = SampleEvent(name="test")
        self.assertIsInstance(event.event_id, str)
        self.assertTrue(len(event.event_id) > 0)

    def test_event_id_unique(self):
        event1 = SampleEvent(name="a")
        event2 = SampleEvent(name="b")
        self.assertNotEqual(event1.event_id, event2.event_id)

    def test_occurred_at_auto_generated_utc(self):
        event = SampleEvent(name="test")
        self.assertIsInstance(event.occurred_at, datetime)
        self.assertEqual(event.occurred_at.tzinfo, timezone.utc)

    def test_event_type_returns_class_name(self):
        event = SampleEvent(name="test")
        self.assertEqual(event.event_type, "SampleEvent")

    def test_to_dict_serializes_correctly(self):
        event = SampleEvent(name="test")
        result = event.to_dict()
        self.assertEqual(result["name"], "test")
        self.assertEqual(result["event_type"], "SampleEvent")
        self.assertIsInstance(result["occurred_at"], str)
        self.assertIn("event_id", result)

    def test_to_dict_datetime_is_iso_format(self):
        event = SampleEvent(name="test")
        result = event.to_dict()
        # Should be parseable as ISO
        datetime.fromisoformat(result["occurred_at"])


if __name__ == "__main__":
    unittest.main()

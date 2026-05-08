"""Collection of common SQLAlchemy models and types."""

import json
from typing import Optional

from sqlalchemy import String, TypeDecorator

from edge_mining.shared.interfaces.config import Configuration


class ConfigurationType(TypeDecorator):
    """Generic SQLAlchemy type for Configuration subclasses.

    This base type handles serialization of Configuration objects to/from JSON strings.
    It converts Configuration instances to JSON when writing to the database and returns
    the JSON string as-is when reading (actual deserialization happens in event listeners).

    This class follows the DRY principle by providing common functionality for all
    Configuration-based types across different domains.
    """

    impl = String
    cache_ok = True

    def process_bind_param(self, value: Optional[Configuration], dialect) -> Optional[str]:
        """Convert Configuration to JSON string before storing in DB.

        Args:
            value: Configuration instance or None
            dialect: SQLAlchemy dialect

        Returns:
            JSON string representation or None
        """
        if value is None:
            return None
        if isinstance(value, str):
            # Already serialized
            return value
        # Serialize config to JSON using the to_dict method
        return json.dumps(value.to_dict())

    def process_result_value(self, value: Optional[str], dialect) -> Optional[str]:
        """Return the JSON string as-is.

        Actual deserialization happens in the event listener specific to each entity.

        Args:
            value: JSON string from database or None
            dialect: SQLAlchemy dialect

        Returns:
            JSON string or None (will be converted to Configuration by event listener)
        """
        return value

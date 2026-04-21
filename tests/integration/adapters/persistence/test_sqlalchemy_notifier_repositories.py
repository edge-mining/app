"""Integration tests for SQLAlchemy Notifier repository."""

import pytest

from edge_mining.adapters.domain.notification.repositories import SqlAlchemyNotifierRepository
from edge_mining.adapters.infrastructure.persistence.sqlalchemy.base import BaseSQLAlchemyRepository
from edge_mining.domain.notification.common import NotificationAdapter
from edge_mining.domain.notification.entities import Notifier
from edge_mining.shared.adapter_configs.notification import DummyNotificationConfig


class TestSqlAlchemyNotifierRepository:
    """Integration tests for SqlAlchemyNotifierRepository."""

    @pytest.fixture
    def repository(self, sqlalchemy_repo: BaseSQLAlchemyRepository) -> SqlAlchemyNotifierRepository:
        """Create a Notifier repository instance."""
        return SqlAlchemyNotifierRepository(db=sqlalchemy_repo)

    def test_add_and_get_notifier_with_enum_adapter(self, repository: SqlAlchemyNotifierRepository):
        """Regression test: enum adapter_type must persist without sqlite binding errors."""
        notifier = Notifier(
            name="Notifier Test",
            adapter_type=NotificationAdapter.DUMMY,
            config=DummyNotificationConfig(message="test"),
        )
        original_id = notifier.id

        # This call used to fail with sqlite3.ProgrammingError when adapter_type was an enum instance.
        repository.add(notifier)

        # Entity should still expose enum type after commit.
        assert notifier.adapter_type == NotificationAdapter.DUMMY

        retrieved = repository.get_by_id(original_id)
        assert retrieved is not None
        assert retrieved.id == original_id
        assert retrieved.name == "Notifier Test"
        assert retrieved.adapter_type == NotificationAdapter.DUMMY
        assert isinstance(retrieved.config, DummyNotificationConfig)

    def test_update_notifier_with_enum_adapter(self, repository: SqlAlchemyNotifierRepository):
        """Regression test: enum adapter_type must remain valid through update commit."""
        notifier = Notifier(
            name="Original Notifier",
            adapter_type=NotificationAdapter.DUMMY,
            config=DummyNotificationConfig(message="before"),
        )
        repository.add(notifier)

        notifier.name = "Updated Notifier"
        notifier.adapter_type = NotificationAdapter.DUMMY
        repository.update(notifier)

        # Entity should still expose enum type after update commit.
        assert notifier.adapter_type == NotificationAdapter.DUMMY

        retrieved = repository.get_by_id(notifier.id)
        assert retrieved is not None
        assert retrieved.name == "Updated Notifier"
        assert retrieved.adapter_type == NotificationAdapter.DUMMY


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

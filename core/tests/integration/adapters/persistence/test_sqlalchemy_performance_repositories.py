"""Integration tests for SQLAlchemy Mining Performance repository."""

import pytest

from edge_mining.adapters.domain.performance.repositories import SqlAlchemyMiningPerformanceTrackerRepository
from edge_mining.adapters.infrastructure.persistence.sqlalchemy.base import BaseSQLAlchemyRepository
from edge_mining.domain.performance.common import MiningPerformanceTrackerAdapter
from edge_mining.domain.performance.entities import MiningPerformanceTracker
from edge_mining.shared.adapter_configs.performance import MiningPerformanceTrackerDummyConfig


class TestSqlAlchemyMiningPerformanceTrackerRepository:
    """Integration tests for SqlAlchemyMiningPerformanceTrackerRepository."""

    @pytest.fixture
    def repository(self, sqlalchemy_repo: BaseSQLAlchemyRepository) -> SqlAlchemyMiningPerformanceTrackerRepository:
        """Create a MiningPerformanceTracker repository instance."""
        return SqlAlchemyMiningPerformanceTrackerRepository(db=sqlalchemy_repo)

    def test_add_and_get_tracker_with_enum_adapter(self, repository: SqlAlchemyMiningPerformanceTrackerRepository):
        """Regression test: enum adapter_type must persist without sqlite binding errors."""
        tracker = MiningPerformanceTracker(
            name="Performance Tracker Test",
            adapter_type=MiningPerformanceTrackerAdapter.DUMMY,
            config=MiningPerformanceTrackerDummyConfig(message="hello"),
        )
        original_id = tracker.id

        repository.add(tracker)

        assert tracker.adapter_type == MiningPerformanceTrackerAdapter.DUMMY

        retrieved = repository.get_by_id(original_id)
        assert retrieved is not None
        assert retrieved.id == original_id
        assert retrieved.name == "Performance Tracker Test"
        assert retrieved.adapter_type == MiningPerformanceTrackerAdapter.DUMMY
        assert isinstance(retrieved.config, MiningPerformanceTrackerDummyConfig)

    def test_update_tracker_with_enum_adapter(self, repository: SqlAlchemyMiningPerformanceTrackerRepository):
        """Regression test: enum adapter_type must remain valid through update commit."""
        tracker = MiningPerformanceTracker(
            name="Original Tracker",
            adapter_type=MiningPerformanceTrackerAdapter.DUMMY,
            config=MiningPerformanceTrackerDummyConfig(message="before"),
        )
        repository.add(tracker)

        tracker.name = "Updated Tracker"
        tracker.adapter_type = MiningPerformanceTrackerAdapter.DUMMY
        repository.update(tracker)

        assert tracker.adapter_type == MiningPerformanceTrackerAdapter.DUMMY

        retrieved = repository.get_by_id(tracker.id)
        assert retrieved is not None
        assert retrieved.name == "Updated Tracker"
        assert retrieved.adapter_type == MiningPerformanceTrackerAdapter.DUMMY


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

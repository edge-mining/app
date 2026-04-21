"""Integration tests for SQLAlchemy Miner Controller repository."""

import pytest

from edge_mining.adapters.domain.miner.repositories import SqlAlchemyMinerControllerRepository
from edge_mining.adapters.infrastructure.persistence.sqlalchemy.base import BaseSQLAlchemyRepository
from edge_mining.domain.miner.common import MinerControllerAdapter
from edge_mining.domain.miner.entities import MinerController
from edge_mining.shared.adapter_configs.miner import MinerControllerDummyConfig


class TestSqlAlchemyMinerControllerRepository:
    """Integration tests for SqlAlchemyMinerControllerRepository."""

    @pytest.fixture
    def repository(self, sqlalchemy_repo: BaseSQLAlchemyRepository) -> SqlAlchemyMinerControllerRepository:
        """Create a MinerController repository instance."""
        return SqlAlchemyMinerControllerRepository(db=sqlalchemy_repo)

    def test_add_and_get_miner_controller_with_enum_adapter(self, repository: SqlAlchemyMinerControllerRepository):
        """Regression test: enum adapter_type must persist without sqlite binding errors."""
        controller = MinerController(
            name="Miner Controller Test",
            adapter_type=MinerControllerAdapter.DUMMY,
            config=MinerControllerDummyConfig(),
        )
        original_id = controller.id

        repository.add(controller)

        assert controller.adapter_type == MinerControllerAdapter.DUMMY

        retrieved = repository.get_by_id(original_id)
        assert retrieved is not None
        assert retrieved.id == original_id
        assert retrieved.name == "Miner Controller Test"
        assert retrieved.adapter_type == MinerControllerAdapter.DUMMY
        assert isinstance(retrieved.config, MinerControllerDummyConfig)

    def test_update_miner_controller_with_enum_adapter(self, repository: SqlAlchemyMinerControllerRepository):
        """Regression test: enum adapter_type must remain valid through update commit."""
        controller = MinerController(
            name="Original Miner Controller",
            adapter_type=MinerControllerAdapter.DUMMY,
            config=MinerControllerDummyConfig(),
        )
        repository.add(controller)

        controller.name = "Updated Miner Controller"
        controller.adapter_type = MinerControllerAdapter.DUMMY
        repository.update(controller)

        assert controller.adapter_type == MinerControllerAdapter.DUMMY

        retrieved = repository.get_by_id(controller.id)
        assert retrieved is not None
        assert retrieved.name == "Updated Miner Controller"
        assert retrieved.adapter_type == MinerControllerAdapter.DUMMY


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

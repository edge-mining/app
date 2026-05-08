"""Unit tests for InMemoryLoadConsumptionModelRepository.get_all."""

import uuid

import pytest

from edge_mining.adapters.domain.home_load.repositories import InMemoryLoadConsumptionModelRepository
from edge_mining.domain.common import EntityId
from edge_mining.domain.home_load.common import EnergyLoadForecastProviderAdapter
from edge_mining.domain.home_load.entities import LoadConsumptionModel


@pytest.fixture
def repo() -> InMemoryLoadConsumptionModelRepository:
    return InMemoryLoadConsumptionModelRepository()


@pytest.fixture
def device_id_a() -> EntityId:
    return EntityId(uuid.uuid4())


@pytest.fixture
def device_id_b() -> EntityId:
    return EntityId(uuid.uuid4())


def _make_model(
    device_id: EntityId,
    adapter: EnergyLoadForecastProviderAdapter = EnergyLoadForecastProviderAdapter.STATSMODELS,
    is_active: bool = False,
) -> LoadConsumptionModel:
    return LoadConsumptionModel(
        device_id=device_id,
        adapter_type=adapter,
        is_active=is_active,
        mae=1.5,
        samples_used=100,
    )


class TestInMemoryLoadConsumptionModelGetAll:
    def test_get_all_empty(self, repo):
        assert repo.get_all() == []

    def test_get_all_returns_all_models(self, repo, device_id_a, device_id_b):
        m1 = _make_model(device_id_a)
        m2 = _make_model(device_id_b, adapter=EnergyLoadForecastProviderAdapter.XGBOOST)
        repo.add(m1)
        repo.add(m2)

        result = repo.get_all()
        assert len(result) == 2
        result_ids = {str(m.id) for m in result}
        assert str(m1.id) in result_ids
        assert str(m2.id) in result_ids

    def test_get_all_filtered_by_device_id(self, repo, device_id_a, device_id_b):
        m1 = _make_model(device_id_a)
        m2 = _make_model(device_id_b)
        m3 = _make_model(device_id_a, adapter=EnergyLoadForecastProviderAdapter.XGBOOST)
        repo.add(m1)
        repo.add(m2)
        repo.add(m3)

        result = repo.get_all(device_id=device_id_a)
        assert len(result) == 2
        for m in result:
            assert str(m.device_id) == str(device_id_a)

    def test_get_all_filtered_returns_empty_for_unknown_device(self, repo, device_id_a):
        repo.add(_make_model(device_id_a))
        unknown = EntityId(uuid.uuid4())
        assert repo.get_all(device_id=unknown) == []

    def test_get_all_returns_deep_copies(self, repo, device_id_a):
        m1 = _make_model(device_id_a)
        repo.add(m1)

        result = repo.get_all()
        assert len(result) == 1
        result[0].mae = 999.0
        # Original should be unchanged
        original = repo.get_by_id(m1.id)
        assert original.mae == 1.5

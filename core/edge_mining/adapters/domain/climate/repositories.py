"""Repository implementations for the Climate domain."""

import copy
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from edge_mining.adapters.infrastructure.persistence.sqlalchemy.base import BaseSQLAlchemyRepository
from edge_mining.domain.climate.entities import ClimateMonitor, ClimateZone
from edge_mining.domain.climate.exceptions import (
    ClimateMonitorAlreadyExistsError,
    ClimateMonitorNotFoundError,
    ClimateZoneAlreadyExistsError,
    ClimateZoneNotFoundError,
)
from edge_mining.domain.climate.ports import ClimateMonitorRepository, ClimateZoneRepository
from edge_mining.domain.common import EntityId


# --- In-Memory Repositories ---


class InMemoryClimateZoneRepository(ClimateZoneRepository):
    """In-memory implementation of ClimateZoneRepository."""

    def __init__(self, initial_zones: Optional[Dict[EntityId, ClimateZone]] = None):
        self._zones: Dict[EntityId, ClimateZone] = copy.deepcopy(initial_zones) if initial_zones else {}

    def add(self, climate_zone: ClimateZone) -> None:
        if climate_zone.id in self._zones:
            raise ClimateZoneAlreadyExistsError(f"Climate zone with id {climate_zone.id} already exists")
        self._zones[climate_zone.id] = copy.deepcopy(climate_zone)

    def get_by_id(self, climate_zone_id: EntityId) -> Optional[ClimateZone]:
        zone = self._zones.get(climate_zone_id)
        return copy.deepcopy(zone) if zone else None

    def get_all(self) -> List[ClimateZone]:
        return [copy.deepcopy(zone) for zone in self._zones.values()]

    def update(self, climate_zone: ClimateZone) -> None:
        if climate_zone.id not in self._zones:
            raise ClimateZoneNotFoundError(f"Climate zone with id {climate_zone.id} not found")
        self._zones[climate_zone.id] = copy.deepcopy(climate_zone)

    def remove(self, climate_zone_id: EntityId) -> None:
        if climate_zone_id not in self._zones:
            raise ClimateZoneNotFoundError(f"Climate zone with id {climate_zone_id} not found")
        del self._zones[climate_zone_id]


class InMemoryClimateMonitorRepository(ClimateMonitorRepository):
    """In-memory implementation of ClimateMonitorRepository."""

    def __init__(self, initial_monitors: Optional[Dict[EntityId, ClimateMonitor]] = None):
        self._monitors: Dict[EntityId, ClimateMonitor] = copy.deepcopy(initial_monitors) if initial_monitors else {}

    def add(self, climate_monitor: ClimateMonitor) -> None:
        if climate_monitor.id in self._monitors:
            raise ClimateMonitorAlreadyExistsError(f"Climate monitor with id {climate_monitor.id} already exists")
        self._monitors[climate_monitor.id] = copy.deepcopy(climate_monitor)

    def get_by_id(self, climate_monitor_id: EntityId) -> Optional[ClimateMonitor]:
        monitor = self._monitors.get(climate_monitor_id)
        return copy.deepcopy(monitor) if monitor else None

    def get_all(self) -> List[ClimateMonitor]:
        return [copy.deepcopy(monitor) for monitor in self._monitors.values()]

    def update(self, climate_monitor: ClimateMonitor) -> None:
        if climate_monitor.id not in self._monitors:
            raise ClimateMonitorNotFoundError(f"Climate monitor with id {climate_monitor.id} not found")
        self._monitors[climate_monitor.id] = copy.deepcopy(climate_monitor)

    def remove(self, climate_monitor_id: EntityId) -> None:
        if climate_monitor_id not in self._monitors:
            raise ClimateMonitorNotFoundError(f"Climate monitor with id {climate_monitor_id} not found")
        del self._monitors[climate_monitor_id]

    def get_by_external_service_id(self, external_service_id: EntityId) -> List[ClimateMonitor]:
        return [
            copy.deepcopy(monitor)
            for monitor in self._monitors.values()
            if monitor.external_service_id == external_service_id
        ]


# --- SQLAlchemy Repositories ---


class SqlAlchemyClimateZoneRepository(ClimateZoneRepository):
    """SQLAlchemy implementation of ClimateZoneRepository."""

    def __init__(self, db: BaseSQLAlchemyRepository):
        self._db = db

    def _get_session(self) -> Session:
        return self._db.get_session()

    def add(self, climate_zone: ClimateZone) -> None:
        session = self._get_session()
        session.add(climate_zone)
        session.commit()

    def get_by_id(self, climate_zone_id: EntityId) -> Optional[ClimateZone]:
        session = self._get_session()
        return session.get(ClimateZone, str(climate_zone_id))

    def get_all(self) -> List[ClimateZone]:
        session = self._get_session()
        return list(session.query(ClimateZone).all())

    def update(self, climate_zone: ClimateZone) -> None:
        session = self._get_session()
        session.merge(climate_zone)
        session.commit()

    def remove(self, climate_zone_id: EntityId) -> None:
        session = self._get_session()
        zone = session.get(ClimateZone, str(climate_zone_id))
        if zone:
            session.delete(zone)
            session.commit()


class SqlAlchemyClimateMonitorRepository(ClimateMonitorRepository):
    """SQLAlchemy implementation of ClimateMonitorRepository."""

    def __init__(self, db: BaseSQLAlchemyRepository):
        self._db = db

    def _get_session(self) -> Session:
        return self._db.get_session()

    def add(self, climate_monitor: ClimateMonitor) -> None:
        session = self._get_session()
        session.add(climate_monitor)
        session.commit()

    def get_by_id(self, climate_monitor_id: EntityId) -> Optional[ClimateMonitor]:
        session = self._get_session()
        return session.get(ClimateMonitor, str(climate_monitor_id))

    def get_all(self) -> List[ClimateMonitor]:
        session = self._get_session()
        return list(session.query(ClimateMonitor).all())

    def update(self, climate_monitor: ClimateMonitor) -> None:
        session = self._get_session()
        session.merge(climate_monitor)
        session.commit()

    def remove(self, climate_monitor_id: EntityId) -> None:
        session = self._get_session()
        monitor = session.get(ClimateMonitor, str(climate_monitor_id))
        if monitor:
            session.delete(monitor)
            session.commit()

    def get_by_external_service_id(self, external_service_id: EntityId) -> List[ClimateMonitor]:
        session = self._get_session()
        return list(
            session.query(ClimateMonitor)
            .filter(ClimateMonitor.external_service_id == str(external_service_id))  # type: ignore
            .all()
        )

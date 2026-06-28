"""
Collection of Aggregate Roots for the Home Consumption Analytics domain
of the Edge Mining application.
"""

from dataclasses import dataclass, field
from typing import List

from edge_mining.domain.common import AggregateRoot, EntityId
from edge_mining.domain.home_load.entities import LoadDevice
from edge_mining.domain.home_load.exceptions import HomeLoadsProfileAddDeviceError


@dataclass
class HomeLoadsProfile(AggregateRoot):
    """Aggregate Root for the Home Loads."""

    name: str = "Default Home Profile"
    devices: List[LoadDevice] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Enforce the device-name uniqueness invariant on construction."""
        seen: set[str] = set()
        for device in self.devices:
            if device.name in seen:
                raise HomeLoadsProfileAddDeviceError(f"Duplicate device name '{device.name}' in profile '{self.name}'.")
            seen.add(device.name)

    def add_device(self, device: LoadDevice) -> None:
        """Append a device enforcing name uniqueness within this profile."""
        if any(existing.name == device.name for existing in self.devices):
            raise HomeLoadsProfileAddDeviceError(
                f"A device named '{device.name}' already exists in profile '{self.name}'."
            )
        self.devices.append(device)

    def remove_device(self, device_id: EntityId) -> LoadDevice:
        """Remove a device by id; raises if not found."""
        for idx, existing in enumerate(self.devices):
            if existing.id == device_id:
                return self.devices.pop(idx)
        from edge_mining.domain.home_load.exceptions import HomeLoadsProfileDeviceNotFoundError

        raise HomeLoadsProfileDeviceNotFoundError(f"Device with id {device_id} not found in profile '{self.name}'.")

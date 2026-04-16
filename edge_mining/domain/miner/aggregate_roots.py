"""Collection of Aggregate Roots for the Mining Device Management domain of the Edge Mining application."""

from dataclasses import dataclass, field
from typing import List, Optional

from edge_mining.domain.common import AggregateRoot, EntityId, Watts
from edge_mining.domain.miner.common import MinerFeatureType
from edge_mining.domain.miner.value_objects import HashRate, MinerFeature


@dataclass
class Miner(AggregateRoot):
    """Aggregate root for a miner.

    Represents the physical mining asset and its intrinsic (static) properties.
    Runtime operational state (status, current hash rate, current power consumption)
    is captured separately in MinerStateSnapshot.

    Aggregates MinerFeature value objects, each representing a capability
    provided by a controller. Multiple controllers can provide features
    to the same miner.
    """

    name: str = ""
    model: Optional[str] = None
    hash_rate_max: Optional[HashRate] = None  # Max hash rate for the miner
    power_consumption_max: Optional[Watts] = None  # Max power consumption for the miner
    active: bool = True  # Is the miner active in the system?

    features: List[MinerFeature] = field(default_factory=list)

    def activate(self):
        """Activate the miner."""
        self.active = True

    def deactivate(self):
        """Deactivate the miner."""
        self.active = False

    # --- Feature management (aggregate root invariants) ---

    def add_feature(self, feature: MinerFeature) -> None:
        """Add a feature to the miner.

        Raises ValueError if a feature with the same (feature_type, controller_id) already exists.
        """
        for existing in self.features:
            if existing.feature_type == feature.feature_type and existing.controller_id == feature.controller_id:
                raise ValueError(
                    f"Feature {feature.feature_type.value} from controller {feature.controller_id} already exists."
                )
        self.features.append(feature)

    def remove_feature(self, feature_type: MinerFeatureType, controller_id: EntityId) -> None:
        """Remove a specific feature by type and controller."""
        self.features = [
            f for f in self.features if not (f.feature_type == feature_type and f.controller_id == controller_id)
        ]

    def remove_features_by_controller(self, controller_id: EntityId) -> None:
        """Remove all features provided by a specific controller."""
        self.features = [f for f in self.features if f.controller_id != controller_id]

    def get_active_feature(self, feature_type: MinerFeatureType) -> Optional[MinerFeature]:
        """Get the highest-priority enabled feature of the given type.

        Returns None if no enabled feature of this type exists.
        """
        candidates = [f for f in self.features if f.feature_type == feature_type and f.enabled]
        if not candidates:
            return None
        return max(candidates, key=lambda f: f.priority)

    def get_features_by_controller(self, controller_id: EntityId) -> List[MinerFeature]:
        """Get all features provided by a specific controller."""
        return [f for f in self.features if f.controller_id == controller_id]

    def get_features_by_type(self, feature_type: MinerFeatureType) -> List[MinerFeature]:
        """Get all features of a specific type (all controllers)."""
        return [f for f in self.features if f.feature_type == feature_type]

    def get_controller_ids(self) -> List[EntityId]:
        """Get all unique controller IDs associated with this miner."""
        return list({f.controller_id for f in self.features})

    def has_feature(self, feature_type: MinerFeatureType) -> bool:
        """Check if the miner has at least one enabled feature of the given type."""
        return any(f.feature_type == feature_type and f.enabled for f in self.features)

    def enable_feature(self, feature_type: MinerFeatureType, controller_id: EntityId) -> None:
        """Enable a specific feature. Replaces the immutable VO with an enabled copy."""
        self.features = [
            MinerFeature(
                feature_type=f.feature_type,
                controller_id=f.controller_id,
                priority=f.priority,
                enabled=True,
            )
            if f.feature_type == feature_type and f.controller_id == controller_id
            else f
            for f in self.features
        ]

    def disable_feature(self, feature_type: MinerFeatureType, controller_id: EntityId) -> None:
        """Disable a specific feature. Replaces the immutable VO with a disabled copy."""
        self.features = [
            MinerFeature(
                feature_type=f.feature_type,
                controller_id=f.controller_id,
                priority=f.priority,
                enabled=False,
            )
            if f.feature_type == feature_type and f.controller_id == controller_id
            else f
            for f in self.features
        ]

    def set_priority(self, feature_type: MinerFeatureType, controller_id: EntityId, priority: int) -> None:
        """Set the priority of a specific feature.

        Raises ValueError if priority is out of range [1, 100].
        """
        if not 1 <= priority <= 100:
            raise ValueError(f"Priority must be between 1 and 100, got {priority}.")
        self.features = [
            MinerFeature(
                feature_type=f.feature_type,
                controller_id=f.controller_id,
                priority=priority,
                enabled=f.enabled,
            )
            if f.feature_type == feature_type and f.controller_id == controller_id
            else f
            for f in self.features
        ]

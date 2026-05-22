"""Validation schemas for optimization unit domain."""

import uuid
from typing import List, Optional

from pydantic import BaseModel, Field, field_serializer, field_validator

from edge_mining.domain.common import EntityId
from edge_mining.domain.optimization_unit.aggregate_roots import EnergyOptimizationUnit


class EnergyOptimizationUnitSchema(BaseModel):
    """Schema for EnergyOptimizationUnit aggregate root with complete validation."""

    id: str = Field(..., description="Unique identifier for the energy optimization unit")
    name: str = Field(default="", description="Energy optimization unit name")
    description: Optional[str] = Field(default=None, description="Energy optimization unit description")
    is_enabled: bool = Field(default=False, description="Whether the optimization unit is enabled")
    policy_id: Optional[str] = Field(default=None, description="ID of the policy to be used for optimization")
    target_miner_ids: List[str] = Field(default_factory=list, description="List of target miner IDs to be controlled")
    energy_source_id: Optional[str] = Field(default=None, description="ID of the energy source to be used")
    performance_tracker_id: Optional[str] = Field(default=None, description="ID of the performance tracker to be used")
    home_loads_profile_id: Optional[str] = Field(default=None, description="ID of the home loads profile to be used")
    notifier_ids: List[str] = Field(default_factory=list, description="List of notifier IDs to be used")
    climate_zone_ids: List[str] = Field(default_factory=list, description="List of climate zone IDs to be monitored")

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Validate that id is a valid UUID string."""
        try:
            uuid.UUID(v)
        except ValueError as exc:
            raise ValueError("id must be a valid UUID string") from exc
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate optimization unit name."""
        v = v.strip()
        if not v:
            v = ""
        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        """Validate optimization unit description."""
        if v is not None:
            v = v.strip()
            if not v:
                v = None
        return v

    @field_validator("policy_id")
    @classmethod
    def validate_policy_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate that policy_id is a valid UUID string if provided."""
        if v is not None:
            try:
                uuid.UUID(v)
            except ValueError as exc:
                raise ValueError("policy_id must be a valid UUID string") from exc
        return v

    @field_validator("target_miner_ids")
    @classmethod
    def validate_target_miner_ids(cls, v: List[str]) -> List[str]:
        """Validate that all target_miner_ids are valid UUID strings."""
        for miner_id in v:
            try:
                uuid.UUID(miner_id)
            except ValueError as exc:
                raise ValueError(f"target_miner_id '{miner_id}' must be a valid UUID string") from exc
        return v

    @field_validator("energy_source_id")
    @classmethod
    def validate_energy_source_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate that energy_source_id is a valid UUID string if provided."""
        if v is not None:
            try:
                uuid.UUID(v)
            except ValueError as exc:
                raise ValueError("energy_source_id must be a valid UUID string") from exc
        return v

    @field_validator("performance_tracker_id")
    @classmethod
    def validate_performance_tracker_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate that performance_tracker_id is a valid UUID string if provided."""
        if v is not None:
            try:
                uuid.UUID(v)
            except ValueError as exc:
                raise ValueError("performance_tracker_id must be a valid UUID string") from exc
        return v

    @field_validator("home_loads_profile_id")
    @classmethod
    def validate_home_loads_profile_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate that home_loads_profile_id is a valid UUID string if provided."""
        if v is not None:
            try:
                uuid.UUID(v)
            except ValueError as exc:
                raise ValueError("home_loads_profile_id must be a valid UUID string") from exc
        return v

    @field_validator("notifier_ids")
    @classmethod
    def validate_notifier_ids(cls, v: List[str]) -> List[str]:
        """Validate that all notifier_ids are valid UUID strings."""
        for notifier_id in v:
            try:
                uuid.UUID(notifier_id)
            except ValueError as exc:
                raise ValueError(f"notifier_id '{notifier_id}' must be a valid UUID string") from exc
        return v

    @field_validator("climate_zone_ids")
    @classmethod
    def validate_climate_zone_ids(cls, v: List[str]) -> List[str]:
        """Validate that all climate_zone_ids are valid UUID strings."""
        for zone_id in v:
            try:
                uuid.UUID(zone_id)
            except ValueError as exc:
                raise ValueError(f"climate_zone_id '{zone_id}' must be a valid UUID string") from exc
        return v

    @classmethod
    def from_model(cls, optimization_unit: EnergyOptimizationUnit) -> "EnergyOptimizationUnitSchema":
        """Create EnergyOptimizationUnitSchema from an EnergyOptimizationUnit domain model instance."""
        return cls(
            id=str(optimization_unit.id),
            name=optimization_unit.name,
            description=optimization_unit.description,
            is_enabled=optimization_unit.is_enabled,
            policy_id=str(optimization_unit.policy_id) if optimization_unit.policy_id else None,
            target_miner_ids=[str(miner_id) for miner_id in optimization_unit.target_miner_ids],
            energy_source_id=str(optimization_unit.energy_source_id) if optimization_unit.energy_source_id else None,
            performance_tracker_id=(
                str(optimization_unit.performance_tracker_id) if optimization_unit.performance_tracker_id else None
            ),
            home_loads_profile_id=(
                str(optimization_unit.home_loads_profile) if optimization_unit.home_loads_profile else None
            ),
            notifier_ids=[str(notifier_id) for notifier_id in optimization_unit.notifier_ids],
            climate_zone_ids=[str(zone_id) for zone_id in optimization_unit.climate_zone_ids],
        )

    @field_serializer("id")
    def serialize_id(self, value: str) -> str:
        """Serialize id field."""
        return str(value)

    @field_serializer("policy_id")
    def serialize_policy_id(self, value: Optional[str]) -> Optional[str]:
        """Serialize policy_id field."""
        return str(value) if value is not None else None

    @field_serializer("target_miner_ids")
    def serialize_target_miner_ids(self, value: List[str]) -> List[str]:
        """Serialize target_miner_ids field."""
        return [str(miner_id) for miner_id in value]

    @field_serializer("energy_source_id")
    def serialize_energy_source_id(self, value: Optional[str]) -> Optional[str]:
        """Serialize energy_source_id field."""
        return str(value) if value is not None else None

    @field_serializer("performance_tracker_id")
    def serialize_performance_tracker_id(self, value: Optional[str]) -> Optional[str]:
        """Serialize performance_tracker_id field."""
        return str(value) if value is not None else None

    @field_serializer("home_loads_profile_id")
    def serialize_home_loads_profile_id(self, value: Optional[str]) -> Optional[str]:
        """Serialize home_loads_profile_id field."""
        return str(value) if value is not None else None

    @field_serializer("notifier_ids")
    def serialize_notifier_ids(self, value: List[str]) -> List[str]:
        """Serialize notifier_ids field."""
        return [str(notifier_id) for notifier_id in value]

    @field_serializer("climate_zone_ids")
    def serialize_climate_zone_ids(self, value: List[str]) -> List[str]:
        """Serialize climate_zone_ids field."""
        return [str(zone_id) for zone_id in value]

    def to_model(self) -> EnergyOptimizationUnit:
        """Convert EnergyOptimizationUnitSchema back to EnergyOptimizationUnit domain model instance."""
        return EnergyOptimizationUnit(
            id=EntityId(uuid.UUID(self.id)),
            name=self.name,
            description=self.description,
            is_enabled=self.is_enabled,
            policy_id=EntityId(uuid.UUID(self.policy_id)) if self.policy_id else None,
            target_miner_ids=[EntityId(uuid.UUID(miner_id)) for miner_id in self.target_miner_ids],
            energy_source_id=EntityId(uuid.UUID(self.energy_source_id)) if self.energy_source_id else None,
            performance_tracker_id=(
                EntityId(uuid.UUID(self.performance_tracker_id)) if self.performance_tracker_id else None
            ),
            home_loads_profile=(
                EntityId(uuid.UUID(self.home_loads_profile_id)) if self.home_loads_profile_id else None
            ),
            notifier_ids=[EntityId(uuid.UUID(notifier_id)) for notifier_id in self.notifier_ids],
            climate_zone_ids=[EntityId(uuid.UUID(zone_id)) for zone_id in self.climate_zone_ids],
        )

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
        validate_assignment = True
        arbitrary_types_allowed = True
        json_encoders = {
            uuid.UUID: str,
        }


class EnergyOptimizationUnitCreateSchema(BaseModel):
    """Schema for creating a new energy optimization unit."""

    name: str = Field(default="", description="Energy optimization unit name")
    description: Optional[str] = Field(default=None, description="Energy optimization unit description")
    policy_id: Optional[str] = Field(default=None, description="ID of the policy to be used for optimization")
    target_miner_ids: List[str] = Field(default_factory=list, description="List of target miner IDs to be controlled")
    energy_source_id: Optional[str] = Field(default=None, description="ID of the energy source to be used")
    performance_tracker_id: Optional[str] = Field(default=None, description="ID of the performance tracker to be used")
    home_loads_profile_id: Optional[str] = Field(default=None, description="ID of the home loads profile to be used")
    notifier_ids: List[str] = Field(default_factory=list, description="List of notifier IDs to be used")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate optimization unit name."""
        v = v.strip()
        if not v:
            v = ""
        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        """Validate optimization unit description."""
        if v is not None:
            v = v.strip()
            if not v:
                v = None
        return v

    @field_validator("policy_id")
    @classmethod
    def validate_policy_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate that policy_id is a valid UUID string if provided."""
        if v is not None:
            try:
                uuid.UUID(v)
            except ValueError as exc:
                raise ValueError("policy_id must be a valid UUID string") from exc
        return v

    @field_validator("target_miner_ids")
    @classmethod
    def validate_target_miner_ids(cls, v: List[str]) -> List[str]:
        """Validate that all target_miner_ids are valid UUID strings."""
        for miner_id in v:
            try:
                uuid.UUID(miner_id)
            except ValueError as exc:
                raise ValueError(f"target_miner_id '{miner_id}' must be a valid UUID string") from exc
        return v

    @field_validator("energy_source_id")
    @classmethod
    def validate_energy_source_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate that energy_source_id is a valid UUID string if provided."""
        if v is not None:
            try:
                uuid.UUID(v)
            except ValueError as exc:
                raise ValueError("energy_source_id must be a valid UUID string") from exc
        return v

    @field_validator("performance_tracker_id")
    @classmethod
    def validate_performance_tracker_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate that performance_tracker_id is a valid UUID string if provided."""
        if v is not None:
            try:
                uuid.UUID(v)
            except ValueError as exc:
                raise ValueError("performance_tracker_id must be a valid UUID string") from exc
        return v

    @field_validator("home_loads_profile_id")
    @classmethod
    def validate_home_loads_profile_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate that home_loads_profile_id is a valid UUID string if provided."""
        if v is not None:
            try:
                uuid.UUID(v)
            except ValueError as exc:
                raise ValueError("home_loads_profile_id must be a valid UUID string") from exc
        return v

    @field_validator("notifier_ids")
    @classmethod
    def validate_notifier_ids(cls, v: List[str]) -> List[str]:
        """Validate that all notifier_ids are valid UUID strings."""
        for notifier_id in v:
            try:
                uuid.UUID(notifier_id)
            except ValueError as exc:
                raise ValueError(f"notifier_id '{notifier_id}' must be a valid UUID string") from exc
        return v

    @field_validator("climate_zone_ids")
    @classmethod
    def validate_climate_zone_ids(cls, v: List[str]) -> List[str]:
        """Validate that all climate_zone_ids are valid UUID strings."""
        for zone_id in v:
            try:
                uuid.UUID(zone_id)
            except ValueError as exc:
                raise ValueError(f"climate_zone_id '{zone_id}' must be a valid UUID string") from exc
        return v

    def to_model(self) -> EnergyOptimizationUnit:
        """Convert EnergyOptimizationUnitCreateSchema to an EnergyOptimizationUnit domain model instance."""
        return EnergyOptimizationUnit(
            id=EntityId(uuid.uuid4()),
            name=self.name,
            description=self.description,
            is_enabled=False,
            policy_id=EntityId(uuid.UUID(self.policy_id)) if self.policy_id else None,
            target_miner_ids=[EntityId(uuid.UUID(miner_id)) for miner_id in self.target_miner_ids],
            energy_source_id=EntityId(uuid.UUID(self.energy_source_id)) if self.energy_source_id else None,
            performance_tracker_id=(
                EntityId(uuid.UUID(self.performance_tracker_id)) if self.performance_tracker_id else None
            ),
            home_loads_profile=(
                EntityId(uuid.UUID(self.home_loads_profile_id)) if self.home_loads_profile_id else None
            ),
            notifier_ids=[EntityId(uuid.UUID(notifier_id)) for notifier_id in self.notifier_ids],
            climate_zone_ids=[EntityId(uuid.UUID(zone_id)) for zone_id in self.climate_zone_ids],
        )

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
        validate_assignment = True
        json_encoders = {
            uuid.UUID: str,
        }


class EnergyOptimizationUnitUpdateSchema(BaseModel):
    """Schema for updating an existing energy optimization unit."""

    name: str = Field(default="", description="Energy optimization unit name")
    description: Optional[str] = Field(default=None, description="Energy optimization unit description")
    policy_id: Optional[str] = Field(default=None, description="ID of the policy to be used for optimization")
    target_miner_ids: List[str] = Field(default_factory=list, description="List of target miner IDs to be controlled")
    energy_source_id: Optional[str] = Field(default=None, description="ID of the energy source to be used")
    performance_tracker_id: Optional[str] = Field(default=None, description="ID of the performance tracker to be used")
    home_loads_profile_id: Optional[str] = Field(default=None, description="ID of the home loads profile to be used")
    notifier_ids: List[str] = Field(default_factory=list, description="List of notifier IDs to be used")
    climate_zone_ids: List[str] = Field(default_factory=list, description="List of climate zone IDs to be monitored")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate optimization unit name."""
        v = v.strip()
        if not v:
            v = ""
        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        """Validate optimization unit description."""
        if v is not None:
            v = v.strip()
            if not v:
                v = None
        return v

    @field_validator("policy_id")
    @classmethod
    def validate_policy_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate that policy_id is a valid UUID string if provided."""
        if v is not None:
            try:
                uuid.UUID(v)
            except ValueError as exc:
                raise ValueError("policy_id must be a valid UUID string") from exc
        return v

    @field_validator("target_miner_ids")
    @classmethod
    def validate_target_miner_ids(cls, v: List[str]) -> List[str]:
        """Validate that all target_miner_ids are valid UUID strings."""
        for miner_id in v:
            try:
                uuid.UUID(miner_id)
            except ValueError as exc:
                raise ValueError(f"target_miner_id '{miner_id}' must be a valid UUID string") from exc
        return v

    @field_validator("energy_source_id")
    @classmethod
    def validate_energy_source_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate that energy_source_id is a valid UUID string if provided."""
        if v is not None:
            try:
                uuid.UUID(v)
            except ValueError as exc:
                raise ValueError("energy_source_id must be a valid UUID string") from exc
        return v

    @field_validator("performance_tracker_id")
    @classmethod
    def validate_performance_tracker_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate that performance_tracker_id is a valid UUID string if provided."""
        if v is not None:
            try:
                uuid.UUID(v)
            except ValueError as exc:
                raise ValueError("performance_tracker_id must be a valid UUID string") from exc
        return v

    @field_validator("home_loads_profile_id")
    @classmethod
    def validate_home_loads_profile_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate that home_loads_profile_id is a valid UUID string if provided."""
        if v is not None:
            try:
                uuid.UUID(v)
            except ValueError as exc:
                raise ValueError("home_loads_profile_id must be a valid UUID string") from exc
        return v

    @field_validator("notifier_ids")
    @classmethod
    def validate_notifier_ids(cls, v: List[str]) -> List[str]:
        """Validate that all notifier_ids are valid UUID strings."""
        for notifier_id in v:
            try:
                uuid.UUID(notifier_id)
            except ValueError as exc:
                raise ValueError(f"notifier_id '{notifier_id}' must be a valid UUID string") from exc
        return v

    @field_validator("climate_zone_ids")
    @classmethod
    def validate_climate_zone_ids(cls, v: List[str]) -> List[str]:
        """Validate that all climate_zone_ids are valid UUID strings."""
        for zone_id in v:
            try:
                uuid.UUID(zone_id)
            except ValueError as exc:
                raise ValueError(f"climate_zone_id '{zone_id}' must be a valid UUID string") from exc
        return v

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
        validate_assignment = True
        json_encoders = {
            uuid.UUID: str,
        }

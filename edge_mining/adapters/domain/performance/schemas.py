"""Validation schemas for the mining performance tracker domain."""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Union, cast

from pydantic import BaseModel, Field, field_serializer, field_validator

from edge_mining.domain.common import EntityId, Timestamp
from edge_mining.domain.miner.value_objects import HashRate
from edge_mining.domain.performance.common import (
    MiningPerformanceTrackerAdapter,
    PayoutFrequency,
    Satoshi,
)
from edge_mining.domain.performance.entities import MiningPerformanceTracker
from edge_mining.domain.performance.value_objects import (
    MiningPerformanceSnapshot,
    MiningReward,
    PayoutSchedule,
    PoolStats,
    PoolWorkerStats,
)
from edge_mining.shared.adapter_configs.performance import (
    MiningPerformanceTrackerBraiinsPoolConfig,
    MiningPerformanceTrackerDummyConfig,
    MiningPerformanceTrackerOceanConfig,
)
from edge_mining.shared.adapter_maps.performance import (
    MINING_PERFORMANCE_TRACKER_CONFIG_TYPE_MAP,
)
from edge_mining.shared.interfaces.config import MiningPerformanceTrackerConfig


class MiningPerformanceTrackerSchema(BaseModel):
    """Schema for MiningPerformanceTracker entity."""

    id: str = Field(..., description="Unique identifier for the tracker")
    name: str = Field(default="", description="Tracker name")
    adapter_type: MiningPerformanceTrackerAdapter = Field(
        default=MiningPerformanceTrackerAdapter.DUMMY,
        description="Type of performance tracker adapter",
    )
    config: dict = Field(default={}, description="Tracker configuration")
    external_service_id: Optional[str] = Field(default=None, description="ID of external service")

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
        """Strip tracker name."""
        return v.strip()

    @field_validator("adapter_type")
    @classmethod
    def validate_adapter_type(cls, v: str) -> MiningPerformanceTrackerAdapter:
        """Validate that adapter_type is a recognized MiningPerformanceTrackerAdapter."""
        adapter_values = [adapter.value for adapter in MiningPerformanceTrackerAdapter]
        if v not in adapter_values:
            raise ValueError(f"adapter_type must be one of {adapter_values}")
        return MiningPerformanceTrackerAdapter(v)

    @field_validator("external_service_id")
    @classmethod
    def validate_external_service_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate external_service_id is a UUID string when provided."""
        if v is not None:
            try:
                uuid.UUID(v)
            except ValueError as exc:
                raise ValueError("external_service_id must be a valid UUID string") from exc
        return v

    @classmethod
    def from_model(cls, tracker: MiningPerformanceTracker) -> "MiningPerformanceTrackerSchema":
        """Create the schema from a MiningPerformanceTracker entity."""
        return cls(
            id=str(tracker.id),
            name=tracker.name,
            adapter_type=tracker.adapter_type,
            config=tracker.config.to_dict() if tracker.config else {},
            external_service_id=str(tracker.external_service_id) if tracker.external_service_id else None,
        )

    @field_serializer("id")
    def serialize_id(self, value: str) -> str:
        """Serialize id field."""
        return str(value)

    @field_serializer("external_service_id")
    def serialize_external_service_id(self, value: Optional[str]) -> Optional[str]:
        """Serialize external_service_id field."""
        return str(value) if value is not None else None

    def to_model(self) -> MiningPerformanceTracker:
        """Convert to a MiningPerformanceTracker entity."""
        configuration: Optional[MiningPerformanceTrackerConfig] = None
        if self.config:
            config_class = MINING_PERFORMANCE_TRACKER_CONFIG_TYPE_MAP.get(self.adapter_type, None)
            if config_class:
                configuration = cast(MiningPerformanceTrackerConfig, config_class.from_dict(self.config))

        return MiningPerformanceTracker(
            id=EntityId(uuid.UUID(self.id)),
            name=self.name,
            adapter_type=self.adapter_type,
            config=configuration,
            external_service_id=EntityId(uuid.UUID(self.external_service_id)) if self.external_service_id else None,
        )

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
        validate_assignment = True
        arbitrary_types_allowed = True
        json_encoders = {
            uuid.UUID: str,
            MiningPerformanceTrackerAdapter: lambda v: v.value,
        }


class MiningPerformanceTrackerCreateSchema(BaseModel):
    """Schema for creating a new mining performance tracker."""

    name: str = Field(default="", description="Tracker name")
    adapter_type: MiningPerformanceTrackerAdapter = Field(
        default=MiningPerformanceTrackerAdapter.DUMMY,
        description="Type of performance tracker adapter",
    )
    config: Optional[dict] = Field(default=None, description="Tracker configuration")
    external_service_id: Optional[str] = Field(default=None, description="ID of external service")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Strip tracker name."""
        return v.strip()

    @field_validator("adapter_type")
    @classmethod
    def validate_adapter_type(cls, v: str) -> MiningPerformanceTrackerAdapter:
        """Validate that adapter_type is a recognized MiningPerformanceTrackerAdapter."""
        adapter_values = [adapter.value for adapter in MiningPerformanceTrackerAdapter]
        if v not in adapter_values:
            raise ValueError(f"adapter_type must be one of {adapter_values}")
        return MiningPerformanceTrackerAdapter(v)

    @field_validator("external_service_id")
    @classmethod
    def validate_external_service_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate external_service_id is a UUID string when provided."""
        if v is not None:
            try:
                uuid.UUID(v)
            except ValueError as exc:
                raise ValueError("external_service_id must be a valid UUID string") from exc
        return v

    def to_model(self) -> MiningPerformanceTracker:
        """Convert to a MiningPerformanceTracker entity (new UUID)."""
        configuration: Optional[MiningPerformanceTrackerConfig] = None
        if self.config:
            config_class = MINING_PERFORMANCE_TRACKER_CONFIG_TYPE_MAP.get(self.adapter_type, None)
            if config_class:
                configuration = cast(MiningPerformanceTrackerConfig, config_class.from_dict(self.config))

        return MiningPerformanceTracker(
            id=EntityId(uuid.uuid4()),
            name=self.name,
            adapter_type=self.adapter_type,
            config=configuration,
            external_service_id=EntityId(uuid.UUID(self.external_service_id)) if self.external_service_id else None,
        )

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
        validate_assignment = True
        json_encoders = {
            uuid.UUID: str,
            MiningPerformanceTrackerAdapter: lambda v: v.value,
        }


class MiningPerformanceTrackerUpdateSchema(BaseModel):
    """Schema for updating an existing mining performance tracker."""

    name: str = Field(default="", description="Tracker name")
    config: Optional[dict] = Field(default=None, description="Tracker configuration")
    external_service_id: Optional[str] = Field(default=None, description="ID of external service")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Strip tracker name."""
        return v.strip()

    @field_validator("external_service_id")
    @classmethod
    def validate_external_service_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate external_service_id is a UUID string when provided."""
        if v is not None:
            try:
                uuid.UUID(v)
            except ValueError as exc:
                raise ValueError("external_service_id must be a valid UUID string") from exc
        return v

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
        validate_assignment = True
        json_encoders = {
            uuid.UUID: str,
        }


class DummyMiningPerformanceTrackerConfigSchema(BaseModel):
    """Schema for the dummy performance tracker configuration."""

    message: str = Field(
        default="This is a dummy performance tracker",
        description="Informational message for the dummy tracker",
    )

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
        validate_assignment = True


class OceanMiningPerformanceTrackerConfigSchema(BaseModel):
    """Schema for the Ocean.xyz performance tracker configuration."""

    bitcoin_address: str = Field(..., description="Bitcoin payout address registered on Ocean")
    api_base_url: str = Field(
        default="https://api.ocean.xyz",
        description="Base URL for the Ocean public API",
    )
    request_timeout_seconds: int = Field(default=10, ge=1, description="HTTP request timeout in seconds")

    @field_validator("bitcoin_address")
    @classmethod
    def validate_bitcoin_address(cls, v: str) -> str:
        """Bitcoin address must not be blank."""
        v = v.strip()
        if not v:
            raise ValueError("bitcoin_address cannot be empty")
        return v

    @field_validator("api_base_url")
    @classmethod
    def validate_api_base_url(cls, v: str) -> str:
        """Base URL must not be blank."""
        v = v.strip()
        if not v:
            raise ValueError("api_base_url cannot be empty")
        return v

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
        validate_assignment = True


class BraiinsPoolMiningPerformanceTrackerConfigSchema(BaseModel):
    """Schema for the Braiins Pool performance tracker configuration."""

    api_token: str = Field(..., description="Access profile token generated in Braiins Pool settings")
    api_base_url: str = Field(
        default="https://pool.braiins.com",
        description="Base URL for the Braiins Pool API",
    )
    request_timeout_seconds: int = Field(default=10, ge=1, description="HTTP request timeout in seconds")

    @field_validator("api_token")
    @classmethod
    def validate_api_token(cls, v: str) -> str:
        """API token must not be blank."""
        v = v.strip()
        if not v:
            raise ValueError("api_token cannot be empty")
        return v

    @field_validator("api_base_url")
    @classmethod
    def validate_api_base_url(cls, v: str) -> str:
        """Base URL must not be blank."""
        v = v.strip()
        if not v:
            raise ValueError("api_base_url cannot be empty")
        return v

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
        validate_assignment = True


MINING_PERFORMANCE_TRACKER_CONFIG_SCHEMA_MAP: Dict[
    type[MiningPerformanceTrackerConfig],
    Union[
        type[DummyMiningPerformanceTrackerConfigSchema],
        type[OceanMiningPerformanceTrackerConfigSchema],
        type[BraiinsPoolMiningPerformanceTrackerConfigSchema],
    ],
] = {
    MiningPerformanceTrackerDummyConfig: DummyMiningPerformanceTrackerConfigSchema,
    MiningPerformanceTrackerOceanConfig: OceanMiningPerformanceTrackerConfigSchema,
    MiningPerformanceTrackerBraiinsPoolConfig: BraiinsPoolMiningPerformanceTrackerConfigSchema,
}


class HashRateSchema(BaseModel):
    """Schema representing a hash rate value."""

    value: float = Field(..., description="Hash rate value")
    unit: str = Field(default="TH/s", description="Hash rate unit")

    def to_model(self) -> HashRate:
        """Convert schema to HashRate value object."""
        return HashRate(value=self.value, unit=self.unit)


class PoolWorkerStatsSchema(BaseModel):
    """Schema for a single worker's pool statistics."""

    worker_name: str
    hashrate: Optional[HashRateSchema] = None
    last_share_at: Optional[datetime] = None
    valid_shares: Optional[int] = None
    stale_shares: Optional[int] = None
    rejected_shares: Optional[int] = None

    @classmethod
    def from_model(cls, worker: PoolWorkerStats) -> "PoolWorkerStatsSchema":
        """Build the schema from a PoolWorkerStats value object."""
        return cls(
            worker_name=worker.worker_name,
            hashrate=HashRateSchema(value=worker.hashrate.value, unit=worker.hashrate.unit)
            if worker.hashrate
            else None,
            last_share_at=worker.last_share_at,
            valid_shares=worker.valid_shares,
            stale_shares=worker.stale_shares,
            rejected_shares=worker.rejected_shares,
        )

    def to_model(self) -> PoolWorkerStats:
        """Convert schema to PoolWorkerStats value object."""
        return PoolWorkerStats(
            worker_name=self.worker_name,
            hashrate=self.hashrate.to_model() if self.hashrate else None,
            last_share_at=Timestamp(self.last_share_at) if self.last_share_at else None,
            valid_shares=self.valid_shares,
            stale_shares=self.stale_shares,
            rejected_shares=self.rejected_shares,
        )


class PoolStatsSchema(BaseModel):
    """Schema for account-level pool statistics."""

    current_hashrate: Optional[HashRateSchema] = None
    average_hashrate_24h: Optional[HashRateSchema] = None
    average_hashrate_7d: Optional[HashRateSchema] = None
    unpaid_balance: Optional[int] = None
    estimated_next_payout: Optional[int] = None
    workers: List[PoolWorkerStatsSchema] = Field(default_factory=list)
    timestamp: datetime

    @classmethod
    def from_model(cls, stats: PoolStats) -> "PoolStatsSchema":
        """Build the schema from a PoolStats value object."""
        return cls(
            current_hashrate=HashRateSchema(value=stats.current_hashrate.value, unit=stats.current_hashrate.unit)
            if stats.current_hashrate
            else None,
            average_hashrate_24h=HashRateSchema(
                value=stats.average_hashrate_24h.value, unit=stats.average_hashrate_24h.unit
            )
            if stats.average_hashrate_24h
            else None,
            average_hashrate_7d=HashRateSchema(
                value=stats.average_hashrate_7d.value, unit=stats.average_hashrate_7d.unit
            )
            if stats.average_hashrate_7d
            else None,
            unpaid_balance=int(stats.unpaid_balance) if stats.unpaid_balance is not None else None,
            estimated_next_payout=int(stats.estimated_next_payout) if stats.estimated_next_payout is not None else None,
            workers=[PoolWorkerStatsSchema.from_model(w) for w in stats.workers],
            timestamp=stats.timestamp,
        )

    def to_model(self) -> PoolStats:
        """Convert schema to PoolStats value object."""
        return PoolStats(
            current_hashrate=self.current_hashrate.to_model() if self.current_hashrate else None,
            average_hashrate_24h=self.average_hashrate_24h.to_model() if self.average_hashrate_24h else None,
            average_hashrate_7d=self.average_hashrate_7d.to_model() if self.average_hashrate_7d else None,
            unpaid_balance=Satoshi(self.unpaid_balance) if self.unpaid_balance is not None else None,
            estimated_next_payout=(
                Satoshi(self.estimated_next_payout) if self.estimated_next_payout is not None else None
            ),
            workers=[w.to_model() for w in self.workers],
            timestamp=Timestamp(self.timestamp),
        )


class MiningRewardSchema(BaseModel):
    """Schema for a single mining reward."""

    amount: int = Field(..., description="Reward amount in satoshi")
    timestamp: datetime

    @classmethod
    def from_model(cls, reward: MiningReward) -> "MiningRewardSchema":
        """Build the schema from a MiningReward value object."""
        return cls(amount=int(reward.amount), timestamp=reward.timestamp)

    def to_model(self) -> MiningReward:
        """Convert schema to MiningReward value object."""
        return MiningReward(amount=Satoshi(self.amount), timestamp=Timestamp(self.timestamp))


class PayoutScheduleSchema(BaseModel):
    """Schema for a payout schedule."""

    frequency: PayoutFrequency = PayoutFrequency.UNKNOWN
    threshold: Optional[int] = None
    next_payout_at: Optional[datetime] = None

    @classmethod
    def from_model(cls, schedule: PayoutSchedule) -> "PayoutScheduleSchema":
        """Build the schema from a PayoutSchedule value object."""
        return cls(
            frequency=schedule.frequency,
            threshold=int(schedule.threshold) if schedule.threshold is not None else None,
            next_payout_at=schedule.next_payout_at,
        )

    def to_model(self) -> PayoutSchedule:
        """Convert schema to PayoutSchedule value object."""
        return PayoutSchedule(
            frequency=self.frequency,
            threshold=Satoshi(self.threshold) if self.threshold is not None else None,
            next_payout_at=Timestamp(self.next_payout_at) if self.next_payout_at else None,
        )


class MiningPerformanceSnapshotSchema(BaseModel):
    """Schema for the consolidated mining performance snapshot."""

    current_hashrate: Optional[HashRateSchema] = None
    pool_stats: Optional[PoolStatsSchema] = None
    payout_schedule: Optional[PayoutScheduleSchema] = None
    timestamp: datetime

    @classmethod
    def from_model(cls, snapshot: MiningPerformanceSnapshot) -> "MiningPerformanceSnapshotSchema":
        """Build the schema from a MiningPerformanceSnapshot value object."""
        return cls(
            current_hashrate=HashRateSchema(value=snapshot.current_hashrate.value, unit=snapshot.current_hashrate.unit)
            if snapshot.current_hashrate
            else None,
            pool_stats=PoolStatsSchema.from_model(snapshot.pool_stats) if snapshot.pool_stats else None,
            payout_schedule=PayoutScheduleSchema.from_model(snapshot.payout_schedule)
            if snapshot.payout_schedule
            else None,
            timestamp=snapshot.timestamp,
        )

    def to_model(self) -> MiningPerformanceSnapshot:
        """Convert schema to MiningPerformanceSnapshot value object."""
        return MiningPerformanceSnapshot(
            current_hashrate=self.current_hashrate.to_model() if self.current_hashrate else None,
            pool_stats=self.pool_stats.to_model() if self.pool_stats else None,
            payout_schedule=self.payout_schedule.to_model() if self.payout_schedule else None,
            timestamp=Timestamp(self.timestamp),
        )

    class Config:
        """Pydantic configuration."""

        use_enum_values = True

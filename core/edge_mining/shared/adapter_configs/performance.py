"""
Collection of adapters configuration for the performace tracker domain
of the Edge Mining application.
"""

from dataclasses import asdict, dataclass

from edge_mining.domain.performance.common import MiningPerformanceTrackerAdapter
from edge_mining.shared.interfaces.config import MiningPerformanceTrackerConfig


@dataclass(frozen=True)
class MiningPerformanceTrackerDummyConfig(MiningPerformanceTrackerConfig):
    """
    Dummy mining performance tracker configuration. It encapsulates the configuration parameters
    to track performance via a dummy adapter.
    """

    message: str = "This is a dummy performance tracker"

    def is_valid(self, adapter_type: MiningPerformanceTrackerAdapter) -> bool:
        """
        Check if the configuration is valid for the given adapter type.
        For Dummy Performance Tracker, it is always valid.
        """
        return adapter_type == MiningPerformanceTrackerAdapter.DUMMY

    def to_dict(self) -> dict:
        """Converts the configuration object into a serializable dictionary"""
        return {**asdict(self)}

    @classmethod
    def from_dict(cls, data: dict):
        """Create a configuration object from a dictionary"""
        return cls(**data)


@dataclass(frozen=True)
class MiningPerformanceTrackerBraiinsPoolConfig(MiningPerformanceTrackerConfig):
    """
    Braiins Pool mining performance tracker configuration.

    Braiins requires an API token that the user generates in
    `Settings > Access Profiles`; the token is sent via the `Pool-Auth-Token` header.
    """

    api_token: str = ""
    api_base_url: str = "https://pool.braiins.com"
    request_timeout_seconds: int = 10

    def is_valid(self, adapter_type: MiningPerformanceTrackerAdapter) -> bool:
        """Check the configuration is valid for a Braiins Pool tracker."""
        if adapter_type != MiningPerformanceTrackerAdapter.BRAIINS_POOL:
            return False
        if not self.api_token or not self.api_token.strip():
            return False
        if not self.api_base_url or not self.api_base_url.strip():
            return False
        if self.request_timeout_seconds <= 0:
            return False
        return True

    def to_dict(self) -> dict:
        """Converts the configuration object into a serializable dictionary"""
        return {**asdict(self)}

    @classmethod
    def from_dict(cls, data: dict):
        """Create a configuration object from a dictionary"""
        return cls(**data)


@dataclass(frozen=True)
class MiningPerformanceTrackerOceanConfig(MiningPerformanceTrackerConfig):
    """
    Ocean.xyz mining performance tracker configuration.

    Ocean identifies users by their payout Bitcoin address; no API token is required
    to access public per-user statistics.
    """

    bitcoin_address: str = ""
    api_base_url: str = "https://api.ocean.xyz"
    request_timeout_seconds: int = 10

    def is_valid(self, adapter_type: MiningPerformanceTrackerAdapter) -> bool:
        """Check the configuration is valid for an Ocean tracker."""
        if adapter_type != MiningPerformanceTrackerAdapter.OCEAN:
            return False
        if not self.bitcoin_address or not self.bitcoin_address.strip():
            return False
        if not self.api_base_url or not self.api_base_url.strip():
            return False
        if self.request_timeout_seconds <= 0:
            return False
        return True

    def to_dict(self) -> dict:
        """Converts the configuration object into a serializable dictionary"""
        return {**asdict(self)}

    @classmethod
    def from_dict(cls, data: dict):
        """Create a configuration object from a dictionary"""
        return cls(**data)

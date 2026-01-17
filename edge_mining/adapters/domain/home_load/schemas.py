"""Validation schemas for home load domain."""

from datetime import datetime
from typing import Dict

from pydantic import BaseModel, Field

from edge_mining.domain.common import Timestamp, Watts
from edge_mining.domain.home_load.value_objects import ConsumptionForecast


class ConsumptionForecastSchema(BaseModel):
    """Schema for ConsumptionForecast value object."""

    predicted_watts: Dict[str, float] = Field(
        default_factory=dict, description="Predicted consumption watts by timestamp (ISO format keys)"
    )
    generated_at: datetime = Field(default_factory=datetime.now, description="When the forecast was generated")

    @classmethod
    def from_model(cls, forecast: ConsumptionForecast) -> "ConsumptionForecastSchema":
        """Create schema from ConsumptionForecast value object."""
        # Convert Timestamp keys to ISO string and Watts values to float
        predicted_watts_dict = {ts.isoformat(): float(watts) for ts, watts in forecast.predicted_watts.items()}
        return cls(
            predicted_watts=predicted_watts_dict,
            generated_at=forecast.generated_at,
        )

    def to_model(self) -> ConsumptionForecast:
        """Convert schema to ConsumptionForecast value object."""
        # Convert ISO string keys back to Timestamp and float values to Watts
        predicted_watts_dict = {
            Timestamp(datetime.fromisoformat(ts)): Watts(watts) for ts, watts in self.predicted_watts.items()
        }
        return ConsumptionForecast(
            predicted_watts=predicted_watts_dict,
            generated_at=Timestamp(self.generated_at),
        )

// id: str = Field(..., description="Unique identifier for the miner")
// name: str = Field(default="", description="Miner name")
// status: MinerStatus = Field(default=MinerStatus.UNKNOWN, description="Current miner status")
// hash_rate: Optional[HashRateSchema] = Field(default=None, description="Current hash rate")
// hash_rate_max: Optional[HashRateSchema] = Field(default=None, description="Maximum hash rate")
// power_consumption: Optional[float] = Field(default=None, description="Current power consumption in Watts")
// power_consumption_max: Optional[float] = Field(default=None, ge=0, description="Maximum power consumption in Watts")
// active: bool = Field(default=True, description="Whether the miner is active in the system")
// controller_id: Optional[str] = Field(default=None, description="ID of the associated Miner controller")

export interface Miner {
  id?: number;
  name: string;
  status: string;
  hash_rate?: number;
  hash_rate_max?: number;
  power_consumption?: number;
  power_consumption_max?: number;
  active: boolean;
  controller_id?: number;
}

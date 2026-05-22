export interface TemperatureSlot {
  start_time: string; // "HH:MM"
  end_time: string; // "HH:MM"
  target_temperature: number;
}

export interface ClimateZone {
  id?: string;
  name: string;
  area_sqm?: number;
  climate_monitor_id?: string;
  temperature_schedule: TemperatureSlot[];
  hysteresis_celsius: number;
  default_target_temperature?: number | null;
}

export interface ClimateZoneReading {
  zone_id: string;
  zone_name: string;
  temperature_celsius: number;
  humidity?: number;
  target_temperature?: number | null;
  hysteresis_celsius?: number | null;
  timestamp: string;
}

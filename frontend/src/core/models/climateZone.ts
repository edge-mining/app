export interface ClimateZone {
  id?: string;
  name: string;
  area_sqm?: number;
  climate_monitor_id?: string;
}

export interface ClimateZoneReading {
  zone_id: string;
  zone_name: string;
  temperature_celsius: number;
  humidity?: number;
  timestamp: string;
}

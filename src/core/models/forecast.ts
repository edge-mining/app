// Forecast Power Point
export interface ForecastPowerPoint {
  timestamp: string; // ISO datetime
  power: number; // Watts
}

// Forecast Interval with computed fields
export interface ForecastInterval {
  start: string; // ISO datetime
  end: string; // ISO datetime
  energy?: number; // WattHours
  energy_remaining?: number; // WattHours
  power_points: ForecastPowerPoint[];
  readonly duration?: number; // Computed: duration in seconds
  readonly avg_power?: number; // Computed: average power in Watts
}

// Sun information with computed fields
export interface Sun {
  dawn: string; // ISO datetime
  sunrise: string; // ISO datetime
  noon: string; // ISO datetime
  midnight: string; // ISO datetime
  sunset: string; // ISO datetime
  dusk: string; // ISO datetime
  daylight: number; // seconds
  night: number; // seconds
  twilight: number; // seconds
  azimuth?: number; // degrees
  zenith?: number; // degrees
  elevation?: number; // degrees
  readonly time_before_sunrise?: number; // Computed: seconds until sunrise
  readonly time_after_sunrise?: number; // Computed: seconds since sunrise
  readonly time_before_sunset?: number; // Computed: seconds until sunset
  readonly time_after_sunset?: number; // Computed: seconds since sunset
}

// Forecast with computed fields
export interface Forecast {
  id: string; // UUID
  timestamp: string; // ISO datetime
  intervals: ForecastInterval[];
  readonly next_hour_power?: number; // Computed: power for next hour (Watts)
  readonly avg_next_4_hours_power?: number; // Computed: average power for next 4 hours (Watts)
  readonly next_hour_energy?: number; // Computed: energy for next hour (WattHours)
}

// Factory functions for computed fields
export function createForecastInterval(data: Omit<ForecastInterval, 'duration' | 'avg_power'>): ForecastInterval {
  return {
    ...data,
    get duration() {
      const start = new Date(data.start).getTime();
      const end = new Date(data.end).getTime();
      return (end - start) / 1000; // seconds
    },
    get avg_power() {
      if (data.power_points.length === 0) return 0;
      const totalPower = data.power_points.reduce((sum, point) => sum + point.power, 0);
      return totalPower / data.power_points.length;
    },
  };
}

export function createSun(data: Omit<Sun, 'time_before_sunrise' | 'time_after_sunrise' | 'time_before_sunset' | 'time_after_sunset'>): Sun {
  return {
    ...data,
    get time_before_sunrise() {
      const now = Date.now();
      const sunrise = new Date(data.sunrise).getTime();
      const diff = (sunrise - now) / 1000;
      return diff > 0 ? diff : undefined;
    },
    get time_after_sunrise() {
      const now = Date.now();
      const sunrise = new Date(data.sunrise).getTime();
      return Math.max(0, (now - sunrise) / 1000);
    },
    get time_before_sunset() {
      const now = Date.now();
      const sunset = new Date(data.sunset).getTime();
      const diff = (sunset - now) / 1000;
      return diff > 0 ? diff : undefined;
    },
    get time_after_sunset() {
      const now = Date.now();
      const sunset = new Date(data.sunset).getTime();
      return Math.max(0, (now - sunset) / 1000);
    },
  };
}

export function createForecast(data: Omit<Forecast, 'next_hour_power' | 'avg_next_4_hours_power' | 'next_hour_energy'>): Forecast {
  return {
    ...data,
    get next_hour_power() {
      if (data.intervals.length === 0) return undefined;
      const now = Date.now();
      const oneHourLater = now + 3600000; // 1 hour in milliseconds

      // Find intervals within the next hour
      const relevantIntervals = data.intervals.filter(interval => {
        const start = new Date(interval.start).getTime();
        const end = new Date(interval.end).getTime();
        return start < oneHourLater && end > now;
      });

      if (relevantIntervals.length === 0) return undefined;

      // Calculate weighted average
      let totalPower = 0;
      let totalDuration = 0;

      for (const interval of relevantIntervals) {
        const start = Math.max(now, new Date(interval.start).getTime());
        const end = Math.min(oneHourLater, new Date(interval.end).getTime());
        const duration = (end - start) / 1000; // seconds

        if (interval.power_points.length > 0) {
          const avgPower = interval.power_points.reduce((sum, p) => sum + p.power, 0) / interval.power_points.length;
          totalPower += avgPower * duration;
          totalDuration += duration;
        }
      }

      return totalDuration > 0 ? totalPower / totalDuration : undefined;
    },
    get avg_next_4_hours_power() {
      if (data.intervals.length === 0) return 0;
      const now = Date.now();
      const fourHoursLater = now + 14400000; // 4 hours in milliseconds

      // Find intervals within the next 4 hours
      const relevantIntervals = data.intervals.filter(interval => {
        const start = new Date(interval.start).getTime();
        const end = new Date(interval.end).getTime();
        return start < fourHoursLater && end > now;
      });

      if (relevantIntervals.length === 0) return 0;

      // Calculate weighted average
      let totalPower = 0;
      let totalDuration = 0;

      for (const interval of relevantIntervals) {
        const start = Math.max(now, new Date(interval.start).getTime());
        const end = Math.min(fourHoursLater, new Date(interval.end).getTime());
        const duration = (end - start) / 1000; // seconds

        if (interval.power_points.length > 0) {
          const avgPower = interval.power_points.reduce((sum, p) => sum + p.power, 0) / interval.power_points.length;
          totalPower += avgPower * duration;
          totalDuration += duration;
        }
      }

      return totalDuration > 0 ? totalPower / totalDuration : 0;
    },
    get next_hour_energy() {
      const nextHourPower = this.next_hour_power;
      return nextHourPower !== undefined ? nextHourPower : 0; // Wh = W (for 1 hour)
    },
  };
}

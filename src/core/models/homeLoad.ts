// Consumption Interval (similar to ForecastInterval but for home load)
export interface ConsumptionInterval {
  start: string; // ISO datetime
  end: string; // ISO datetime
  energy?: number; // WattHours
  energy_remaining?: number; // WattHours
  power_points: ConsumptionPowerPoint[];
  readonly duration?: number; // Computed: duration in seconds
  readonly avg_power?: number; // Computed: average power in Watts
}

// Consumption Power Point
export interface ConsumptionPowerPoint {
  timestamp: string; // ISO datetime
  power: number; // Watts
}

// Consumption Forecast
export interface ConsumptionForecast {
  id: string; // UUID
  timestamp: string; // ISO datetime
  intervals: ConsumptionInterval[];
  readonly next_hour_consumption?: number; // Computed: consumption for next hour (Watts)
  readonly avg_next_4_hours_consumption?: number; // Computed: average consumption for next 4 hours (Watts)
  readonly next_hour_energy?: number; // Computed: energy for next hour (WattHours)
}

// Factory functions for computed fields
export function createConsumptionInterval(data: Omit<ConsumptionInterval, 'duration' | 'avg_power'>): ConsumptionInterval {
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

export function createConsumptionForecast(data: Omit<ConsumptionForecast, 'next_hour_consumption' | 'avg_next_4_hours_consumption' | 'next_hour_energy'>): ConsumptionForecast {
  return {
    ...data,
    get next_hour_consumption() {
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
    get avg_next_4_hours_consumption() {
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
      const nextHourConsumption = this.next_hour_consumption;
      return nextHourConsumption !== undefined ? nextHourConsumption : 0; // Wh = W (for 1 hour)
    },
  };
}

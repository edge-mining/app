import { defineStore } from "pinia";
import { ref } from "vue";
import type { DecisionalContext } from "../models/policy";
import type { ForecastPowerPoint } from "../models/forecast";

export interface DashboardEvent {
  id: string;
  type: "miner_start" | "miner_stop" | "status_change" | "rule_triggered";
  message: string;
  timestamp: Date;
  icon?: string;
}

export interface TimeSeriesPoint {
  time: number; // unix seconds
  value: number;
}

export interface MinerOnOffEvent {
  time: number; // unix seconds
  minerName: string;
  action: "on" | "off";
}

const MAX_POINTS = 360; // ~30 min at 5s intervals
const MAX_EVENTS = 50;
const MAX_ONOFF_EVENTS = 100;

export const useDashboardStore = defineStore("dashboard", () => {
  const hashRateSeries = ref<TimeSeriesPoint[]>([]);
  const powerSeries = ref<TimeSeriesPoint[]>([]);
  const energyProductionSeries = ref<TimeSeriesPoint[]>([]);
  const batterySOCSeries = ref<TimeSeriesPoint[]>([]);
  const batteryPowerSeries = ref<TimeSeriesPoint[]>([]);
  const gridPowerSeries = ref<TimeSeriesPoint[]>([]);
  const consumptionSeries = ref<TimeSeriesPoint[]>([]);
  const events = ref<DashboardEvent[]>([]);
  const minerOnOffEvents = ref<MinerOnOffEvent[]>([]);
  const previousMinerStatuses = ref<Map<string, string>>(new Map());
  const latestDecisionalContexts = ref<Map<string, DecisionalContext>>(new Map());
  const forecastPowerPoints = ref<ForecastPowerPoint[]>([]);
  let eventCounter = 0;

  type SeriesName = "hashRate" | "power" | "energyProduction" | "batterySOC" | "batteryPower" | "gridPower" | "consumption";

  const seriesMap: Record<SeriesName, typeof hashRateSeries> = {
    hashRate: hashRateSeries,
    power: powerSeries,
    energyProduction: energyProductionSeries,
    batterySOC: batterySOCSeries,
    batteryPower: batteryPowerSeries,
    gridPower: gridPowerSeries,
    consumption: consumptionSeries,
  };

  function addSeriesPoint(
    series: SeriesName,
    point: TimeSeriesPoint
  ) {
    const target = seriesMap[series];
    const existing = target.value;
    // Skip if any existing point already has this timestamp
    if (existing.some((p) => p.time === point.time)) return;
    target.value = [...existing, point].slice(-MAX_POINTS);
  }

  function addEvent(event: Omit<DashboardEvent, "id">) {
    eventCounter++;
    events.value.unshift({ ...event, id: `evt-${eventCounter}` });
    if (events.value.length > MAX_EVENTS) {
      events.value = events.value.slice(0, MAX_EVENTS);
    }
  }

  function addMinerOnOffEvent(event: MinerOnOffEvent) {
    minerOnOffEvents.value = [
      ...minerOnOffEvents.value,
      event,
    ].slice(-MAX_ONOFF_EVENTS);
  }

  return {
    hashRateSeries,
    powerSeries,
    energyProductionSeries,
    batterySOCSeries,
    batteryPowerSeries,
    gridPowerSeries,
    consumptionSeries,
    events,
    minerOnOffEvents,
    previousMinerStatuses,
    latestDecisionalContexts,
    forecastPowerPoints,
    addSeriesPoint,
    addEvent,
    addMinerOnOffEvent,
  };
});

import { defineStore } from "pinia";
import { ref } from "vue";

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
  const events = ref<DashboardEvent[]>([]);
  const minerOnOffEvents = ref<MinerOnOffEvent[]>([]);
  const previousMinerStatuses = ref<Map<string, string>>(new Map());
  let eventCounter = 0;

  function addSeriesPoint(
    series: "hashRate" | "power",
    point: TimeSeriesPoint
  ) {
    const target =
      series === "hashRate" ? hashRateSeries : powerSeries;
    target.value = [...target.value, point].slice(-MAX_POINTS);
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
    events,
    minerOnOffEvents,
    previousMinerStatuses,
    addSeriesPoint,
    addEvent,
    addMinerOnOffEvent,
  };
});

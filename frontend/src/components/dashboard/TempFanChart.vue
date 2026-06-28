<script setup lang="ts">
import { computed } from "vue";
import VueApexCharts from "vue3-apexcharts";
import type { TimeSeriesPoint } from "../../core/composables/useDashboardPolling";

const props = withDefaults(
  defineProps<{
    chipTempData: TimeSeriesPoint[];
    boardTempData: TimeSeriesPoint[];
    internalFanData: TimeSeriesPoint[];
    externalFanData: TimeSeriesPoint[];
    height?: number | string;
    chipTempColor?: string;
    boardTempColor?: string;
    internalFanColor?: string;
    externalFanColor?: string;
    range?: number;
  }>(),
  {
    height: 160,
    chipTempColor: "rgba(248, 113, 113, 0.9)",
    boardTempColor: "rgba(251, 146, 60, 0.9)",
    internalFanColor: "rgba(56, 189, 248, 0.9)",
    externalFanColor: "rgba(129, 140, 248, 0.9)",
    range: 10 * 60 * 1000,
  }
);

const hasTemp = computed(() => props.chipTempData.length > 0 || props.boardTempData.length > 0);
const hasFan = computed(() => props.internalFanData.length > 0 || props.externalFanData.length > 0);
const dualAxis = computed(() => hasTemp.value && hasFan.value);

interface SeriesEntry {
  name: string;
  data: { x: number; y: number }[];
  kind: "temp" | "fan";
  color: string;
}

const activeSeries = computed<SeriesEntry[]>(() => {
  const result: SeriesEntry[] = [];
  if (props.chipTempData.length > 0) {
    result.push({
      name: "Chip Temp",
      data: props.chipTempData.map((p) => ({ x: p.time * 1000, y: p.value })),
      kind: "temp",
      color: props.chipTempColor,
    });
  }
  if (props.boardTempData.length > 0) {
    result.push({
      name: "Board Temp",
      data: props.boardTempData.map((p) => ({ x: p.time * 1000, y: p.value })),
      kind: "temp",
      color: props.boardTempColor,
    });
  }
  if (props.internalFanData.length > 0) {
    result.push({
      name: "Internal Fan",
      data: props.internalFanData.map((p) => ({ x: p.time * 1000, y: p.value })),
      kind: "fan",
      color: props.internalFanColor,
    });
  }
  if (props.externalFanData.length > 0) {
    result.push({
      name: "External Fan",
      data: props.externalFanData.map((p) => ({ x: p.time * 1000, y: p.value })),
      kind: "fan",
      color: props.externalFanColor,
    });
  }
  return result;
});

const series = computed(() =>
  activeSeries.value.map((s) => ({ name: s.name, data: s.data }))
);

const colors = computed(() => activeSeries.value.map((s) => s.color));

function formatTemp(v: number): string {
  return `${v.toFixed(1)} °C`;
}

function formatFan(v: number): string {
  return `${Math.round(v)} RPM`;
}

// Build one yaxis entry per series so ApexCharts maps them correctly.
// Duplicate axes on the same side get show:false to avoid label clutter.
const yaxisConfig = computed(() => {
  if (activeSeries.value.length === 0) return {};
  if (!dualAxis.value) {
    // Single axis mode: all series share one axis
    const isTempOnly = hasTemp.value;
    return activeSeries.value.map((_, i) => ({
      show: i === 0,
      seriesName: activeSeries.value[0].name,
      decimalsInFloat: isTempOnly ? 1 : 0,
      labels: {
        show: i === 0,
        style: { colors: "rgba(255,255,255,0.3)", fontSize: "10px" },
        formatter: isTempOnly ? formatTemp : formatFan,
      },
      title: { text: undefined },
    }));
  }

  // Dual axis mode: temp on left, fan on right
  let tempPrimaryName: string | undefined;
  let fanPrimaryName: string | undefined;

  return activeSeries.value.map((s) => {
    if (s.kind === "temp") {
      const isFirst = !tempPrimaryName;
      if (isFirst) tempPrimaryName = s.name;
      return {
        show: isFirst,
        seriesName: tempPrimaryName,
        opposite: false,
        decimalsInFloat: 1,
        labels: {
          show: isFirst,
          style: { colors: "rgba(255,255,255,0.3)", fontSize: "10px" },
          formatter: formatTemp,
        },
        title: { text: undefined },
      };
    } else {
      const isFirst = !fanPrimaryName;
      if (isFirst) fanPrimaryName = s.name;
      return {
        show: isFirst,
        seriesName: fanPrimaryName,
        opposite: true,
        decimalsInFloat: 0,
        labels: {
          show: isFirst,
          style: { colors: "rgba(255,255,255,0.3)", fontSize: "10px" },
          formatter: formatFan,
        },
        title: { text: undefined },
      };
    }
  });
});

const chartOptions = computed(() => {
  // Force re-compute on data changes
  void props.chipTempData;
  void props.boardTempData;
  void props.internalFanData;
  void props.externalFanData;

  return {
    chart: {
      id: "temp-fan-chart",
      type: "line" as const,
      height: props.height,
      toolbar: { show: false },
      zoom: { enabled: false },
      animations: {
        enabled: true,
        easing: "linear" as const,
        dynamicAnimation: { enabled: true, speed: 1000 },
      },
      background: "transparent",
      fontFamily: "inherit",
      selection: { enabled: false },
    },
    stroke: {
      curve: "smooth" as const,
      width: 2,
    },
    fill: { opacity: 0 },
    colors: colors.value,
    grid: {
      borderColor: "rgba(255,255,255,0.04)",
      strokeDashArray: 3,
      xaxis: { lines: { show: true } },
      yaxis: { lines: { show: true } },
      padding: { left: 4, right: 4, top: 0, bottom: 0 },
    },
    xaxis: {
      type: "datetime" as const,
      range: props.range,
      labels: {
        show: true,
        style: { colors: "rgba(255,255,255,0.3)", fontSize: "10px" },
        datetimeFormatter: { hour: "HH:mm", minute: "HH:mm" },
      },
      axisBorder: { show: false },
      axisTicks: { show: false },
      tooltip: { enabled: false },
    },
    yaxis: yaxisConfig.value,
    dataLabels: { enabled: false },
    tooltip: {
      enabled: true,
      shared: true,
      intersect: false,
      followCursor: true,
      theme: "dark" as const,
      x: { show: true, format: "HH:mm:ss" },
      y: {
        formatter: (v: number, opts?: { seriesIndex?: number }) => {
          if (opts?.seriesIndex != null) {
            const s = activeSeries.value[opts.seriesIndex];
            return s?.kind === "fan" ? formatFan(v) : formatTemp(v);
          }
          return formatTemp(v);
        },
      },
      marker: { show: true },
    },
    legend: {
      show: true,
      position: "top" as const,
      horizontalAlign: "right" as const,
      fontSize: "10px",
      labels: { colors: "rgba(255,255,255,0.5)" },
      markers: { size: 6, shape: "circle" as const },
      itemMargin: { horizontal: 8 },
    },
    markers: {
      size: 0,
      colors: colors.value,
      strokeColors: "#fff",
      strokeWidth: 1,
      hover: { size: 4, sizeOffset: 2 },
    },
  };
});
</script>

<template>
  <div class="temp-fan-chart-wrapper">
    <VueApexCharts
      type="line"
      :height="height === '100%' ? '100%' : height"
      :width="'100%'"
      :options="chartOptions"
      :series="series"
    />
  </div>
</template>

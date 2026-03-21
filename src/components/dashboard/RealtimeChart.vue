<script setup lang="ts">
import { computed } from "vue";
import VueApexCharts from "vue3-apexcharts";
import type { TimeSeriesPoint } from "../../core/composables/useDashboardPolling";
import type { MinerOnOffEvent } from "../../core/stores/dashboardStore";

const props = withDefaults(
  defineProps<{
    data: TimeSeriesPoint[];
    seriesName?: string;
    height?: number | string;
    lineColor?: string;
    range?: number;
    formatValue?: (v: number) => string;
    minerEvents?: MinerOnOffEvent[];
    showMinerEvents?: boolean;
  }>(),

  {
    height: 160,
    seriesName: "Value",
    lineColor: "rgba(38, 198, 218, 1)",
    range: 10 * 60 * 1000,
    showMinerEvents: true,
  }
);


const series = computed(() => [
  {
    name: props.seriesName,
    data: props.data.map((p) => ({ x: p.time * 1000, y: p.value })),
  },
]);

const annotations = computed(() => {
  if (!props.showMinerEvents || !props.minerEvents?.length) return {};
  return {
    xaxis: props.minerEvents.map((evt) => ({
      x: evt.time * 1000,
      borderColor: evt.action === 'on' ? 'rgba(52, 211, 153, 0.7)' : 'rgba(248, 113, 113, 0.7)',
      strokeDashArray: 3,
      label: {
        text: `${evt.minerName} ${evt.action.toUpperCase()}`,
        orientation: 'horizontal' as const,
        borderColor: 'transparent',
        style: {
          background: evt.action === 'on' ? 'rgba(52, 211, 153, 0.15)' : 'rgba(248, 113, 113, 0.15)',
          color: evt.action === 'on' ? '#34d399' : '#f87171',
          fontSize: '9px',
          padding: { left: 4, right: 4, top: 2, bottom: 2 },
        },
      },
    })),
  };
});

const chartOptions = computed(() => ({
  chart: {
    id: props.seriesName?.replace(/\s+/g, '-').toLowerCase() || 'realtime-chart',
    type: "line" as const,
    height: props.height,
    toolbar: { show: false },
    zoom: { enabled: false },
    animations: {
      enabled: true,
      easing: "linear" as const,
      dynamicAnimation: {
        enabled: true,
        speed: 1000
      },
    },
    background: "transparent",
    fontFamily: "inherit",
    selection: { enabled: false }, // Disable selection zoom
  },
  stroke: {
    curve: "smooth" as const,
    width: 2,
  },
  fill: { opacity: 0 },
  colors: [props.lineColor],
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
      datetimeFormatter: { hour: "HH:mm", minute: "mm:ss" }, // Detailed time
    },
    axisBorder: { show: false },
    axisTicks: { show: false },
    tooltip: { enabled: false } // Disable x-axis tooltip (crosshair label) to cleaner look
  },
  yaxis: {
    labels: {
      show: true,
      style: { colors: "rgba(255,255,255,0.3)", fontSize: "10px" },
      formatter: props.formatValue ?? ((v: number) => v.toFixed(1)),
    },
  },
  dataLabels: { enabled: false },
  tooltip: {
    enabled: true,
    shared: false,
    intersect: false,
    theme: "dark" as const,
    x: { show: true, format: "HH:mm:ss" },
    y: {
      formatter: props.formatValue ?? ((v: number) => v.toFixed(1)),
    },
    marker: { show: true },
  },



  annotations: annotations.value,
  legend: { show: false },
  markers: {
    size: 0, // No markers by default
    colors: [props.lineColor],
    strokeColors: '#fff',
    strokeWidth: 1,
    hover: { size: 4, sizeOffset: 2 }, // Visible on hover
  },
}));

</script>

<template>
  <div class="realtime-chart-wrapper" :class="{ 'h-full w-full': height === '100%' }">
    <VueApexCharts
      type="line"
      :height="height === '100%' ? '100%' : height"
      :width="'100%'"
      :options="chartOptions"
      :series="series"
    />
  </div>
</template>

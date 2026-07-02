<script setup lang="ts">
import { computed } from "vue";
import VueApexCharts from "vue3-apexcharts";
import type { ApexFormatterOpts } from "apexcharts";

export interface ForecastIntervalData {
  /** Start of the interval (unix ms) */
  time: number;
  /** Energy in Wh for this interval */
  energy: number;
  /** Max power in W during this interval */
  maxPower: number;
}

const props = withDefaults(
  defineProps<{
    data: ForecastIntervalData[];
    height?: number | string;
  }>(),
  {
    height: 160,
  }
);

function formatEnergyValue(v: number): string {
  if (v <= 0) return "0 Wh";
  if (v >= 1000000) return `${parseFloat((v / 1000000).toFixed(2))} MWh`;
  if (v >= 1000) return `${parseFloat((v / 1000).toFixed(2))} kWh`;
  return `${Math.round(v)} Wh`;
}

function formatPowerValue(v: number): string {
  if (v === 0) return "0 W";
  const abs = Math.abs(v);
  const sign = v < 0 ? "-" : "";
  if (abs >= 1000000) return `${sign}${parseFloat((abs / 1000000).toFixed(2))} MW`;
  if (abs >= 1000) return `${sign}${parseFloat((abs / 1000).toFixed(2))} kW`;
  return `${sign}${Math.round(abs)} W`;
}

const series = computed(() => {
  return [
    {
      name: "Energy",
      type: "line",
      data: props.data.map((p) => ({ x: p.time, y: p.energy })),
    },
    {
      name: "Max Power",
      type: "column",
      data: props.data.map((p) => ({ x: p.time, y: p.maxPower })),
    },
  ];
});

const chartOptions = computed(() => {
  void props.data;

  return {
    chart: {
      id: "forecast-energy-chart",
      type: "line" as const,
      height: props.height,
      toolbar: { show: false },
      zoom: { enabled: false },
      animations: { enabled: true, easing: "easeinout" as const, speed: 500 },
      background: "transparent",
      fontFamily: "inherit",
      selection: { enabled: false },
      stacked: false,
    },
    stroke: {
      width: [3, 0],
      curve: "smooth" as const,
    },
    fill: {
      opacity: [0.1, 0.7],
      type: ["gradient", "solid"],
      gradient: {
        shade: "dark",
        type: "vertical",
        opacityFrom: 0.3,
        opacityTo: 0.05,
      },
    },
    colors: ["rgba(129, 140, 248, 0.9)", "rgba(250, 204, 21, 0.5)"],
    plotOptions: {
      bar: {
        columnWidth: "60%",
        borderRadius: 2,
      },
    },
    grid: {
      borderColor: "rgba(255,255,255,0.04)",
      strokeDashArray: 3,
      xaxis: { lines: { show: true } },
      yaxis: { lines: { show: true } },
      padding: { left: 4, right: 4, top: 0, bottom: 0 },
    },
    xaxis: {
      type: "datetime" as const,
      labels: {
        show: true,
        style: { colors: "rgba(255,255,255,0.3)", fontSize: "10px" },
        datetimeFormatter: { hour: "HH:mm", day: "dd MMM" },
      },
      axisBorder: { show: false },
      axisTicks: { show: false },
      tooltip: { enabled: false },
    },
    yaxis: [
      {
        seriesName: "Energy",
        decimalsInFloat: 0,
        labels: {
          show: true,
          style: { colors: "rgba(129, 140, 248, 0.5)", fontSize: "10px" },
          formatter: (v: number) => formatEnergyValue(v),
        },
        title: { text: undefined },
      },
      {
        seriesName: "Max Power",
        opposite: true,
        decimalsInFloat: 0,
        labels: {
          show: true,
          style: { colors: "rgba(250, 204, 21, 0.5)", fontSize: "10px" },
          formatter: (v: number) => formatPowerValue(v),
        },
        title: { text: undefined },
      },
    ],
    dataLabels: { enabled: false },
    tooltip: {
      enabled: true,
      shared: true,
      intersect: false,
      followCursor: true,
      theme: "dark" as const,
      x: { show: true, format: "dd MMM HH:mm" },
      y: {
        formatter: (v: number, opts?: ApexFormatterOpts) => {
          if (opts?.seriesIndex === 1) return formatPowerValue(v);
          return formatEnergyValue(v);
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
      size: [3, 0],
      colors: ["rgba(129, 140, 248, 0.9)"],
      strokeColors: "#fff",
      strokeWidth: 1,
      hover: { size: 5, sizeOffset: 2 },
    },
  };
});
</script>

<template>
  <div class="forecast-chart-wrapper">
    <VueApexCharts
      type="line"
      :height="height"
      :width="'100%'"
      :options="chartOptions"
      :series="series"
    />
  </div>
</template>

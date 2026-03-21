<script setup lang="ts">
import { ref, computed, type Component } from "vue";
import { PhChartLine, PhArrowsOutSimple, PhArrowsInSimple, PhMapPin } from "@phosphor-icons/vue";
import { useWindowSize } from "../../core/composables/useWindowSize";

const props = withDefaults(
  defineProps<{
    title: string;
    icon?: Component;
    iconColor?: string;
    /** Height in pixels for the chart area */
    chartHeight?: number;
    /** Whether this panel has data to display */
    hasData?: boolean;
    /** Whether the maximize feature is enabled */
    maximizable?: boolean;
  }>(),
  {
    chartHeight: 180,
    hasData: false,
    iconColor: "text-base-content/40",
    maximizable: true,
  }
);

const isExpanded = ref(false);
const showMinerEvents = ref(true);
const { height: windowHeight } = useWindowSize();

// Header ~45px + padding inset 16px*2 + chart area padding ~24px
const expandedChartHeight = computed(() => windowHeight.value - 32 - 45 - 24);

function toggleMaximize() {
  isExpanded.value = !isExpanded.value;
}
</script>

<template>
  <div 
    class="chart-panel rounded-xl border border-base-300/20 bg-base-100/30 backdrop-blur-sm overflow-hidden transition-all duration-300"
    :class="{ 
      'fixed inset-4 z-50 bg-base-100/95 shadow-2xl flex flex-col': isExpanded, 
      'relative': !isExpanded 
    }"
  >
    <!-- Header -->
    <div class="flex items-center justify-between px-4 py-3 border-b border-base-300/10 shrink-0">
      <div class="flex items-center gap-2">
        <component :is="icon || PhChartLine" :size="16" :class="iconColor" />
        <span class="text-sm font-medium text-base-content/70">{{ title }}</span>
      </div>
      <div class="flex items-center gap-3">
        <slot name="header-actions">
          <span class="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-base-content/25">
            <span v-if="hasData" class="relative flex h-2 w-2">
              <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
              <span class="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
            </span>
            Live
          </span>
        </slot>
        
        <!-- Toggle Miner Events -->
        <button 
          v-if="hasData"
          @click="showMinerEvents = !showMinerEvents"
          class="flex items-center justify-center w-6 h-6 rounded hover:bg-base-content/10 transition-colors"
          :class="showMinerEvents ? 'text-base-content/60' : 'text-base-content/20'"
          title="Toggle miner on/off markers"
        >
          <PhMapPin :size="14" :weight="showMinerEvents ? 'fill' : 'regular'" />
        </button>

        <!-- Maximize Button (Desktop/Tablet) -->
        <button 
          v-if="maximizable" 
          @click="toggleMaximize"
          class="hidden md:flex items-center justify-center w-6 h-6 rounded hover:bg-base-content/10 text-base-content/40 transition-colors"
          :title="isExpanded ? 'Minimize' : 'Maximize'"
        >
          <component :is="isExpanded ? PhArrowsInSimple : PhArrowsOutSimple" :size="14" />
        </button>
      </div>
    </div>

    <!-- Chart Area -->
    <div 
      class="px-4 py-3 transition-all duration-300" 
      :class="{ 'flex-1 min-h-0 h-0': isExpanded }"
      :style="!isExpanded ? { minHeight: `${chartHeight}px` } : {}"
    >
      <slot :expanded="isExpanded" :expandedHeight="expandedChartHeight" :showMinerEvents="showMinerEvents">
        <!-- Default placeholder when no data -->
        <div
          v-if="!hasData"
          class="h-full flex flex-col items-center justify-center gap-2"
          :style="{ minHeight: `${chartHeight - 24}px` }"
        >
          <div class="chart-placeholder w-full" :style="{ height: `${chartHeight - 60}px` }">
            <!-- Simulated chart lines -->
            <svg class="w-full h-full" preserveAspectRatio="none" viewBox="0 0 200 80">
              <defs>
                <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stop-color="currentColor" stop-opacity="0.15" />
                  <stop offset="100%" stop-color="currentColor" stop-opacity="0" />
                </linearGradient>
              </defs>
              <!-- Grid lines -->
              <line x1="0" y1="20" x2="200" y2="20" stroke="currentColor" stroke-opacity="0.05" />
              <line x1="0" y1="40" x2="200" y2="40" stroke="currentColor" stroke-opacity="0.05" />
              <line x1="0" y1="60" x2="200" y2="60" stroke="currentColor" stroke-opacity="0.05" />
              <!-- Placeholder wave -->
              <path
                d="M0,60 Q25,55 50,45 T100,35 T150,50 T200,30"
                fill="none"
                stroke="currentColor"
                stroke-opacity="0.12"
                stroke-width="1.5"
                stroke-dasharray="4,3"
              />
              <path
                d="M0,60 Q25,55 50,45 T100,35 T150,50 T200,30 L200,80 L0,80 Z"
                fill="url(#chartGradient)"
                opacity="0.3"
              />
            </svg>
          </div>
          <span class="text-[11px] text-base-content/20">Waiting for data...</span>
        </div>
      </slot>
    </div>
  </div>
</template>

<style scoped>
.chart-panel {
  transition: border-color 0.2s ease;
}
.chart-panel:hover {
  border-color: oklch(50% 0 0 / 0.25);
}
</style>

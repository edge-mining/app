<script setup lang="ts">
import type { Component } from "vue";

defineProps<{
  label: string;
  value: string | number;
  subValue?: string;
  icon: Component;
  iconColor?: string;
  iconBgColor?: string;
  valueColor?: string;
  pulse?: boolean;
}>();
</script>

<template>
  <div class="kpi-card flex items-center gap-3 rounded-xl border border-base-300/20 bg-base-100/40 px-4 py-3 backdrop-blur-sm">
    <!-- Icon -->
    <div
      class="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg"
      :class="iconBgColor || 'bg-primary/15'"
    >
      <component :is="icon" :size="20" weight="duotone" :class="iconColor || 'text-primary'" />
    </div>

    <!-- Value -->
    <div class="min-w-0 flex-1">
      <div class="text-[11px] uppercase tracking-wider text-base-content/40 mb-0.5 truncate">
        {{ label }}
      </div>
      <div class="flex items-baseline gap-1.5">
        <span
          class="text-xl font-bold leading-none tabular-nums"
          :class="valueColor || 'text-base-content'"
        >
          {{ value }}
        </span>
        <span v-if="subValue" class="text-xs text-base-content/40 truncate">
          {{ subValue }}
        </span>
      </div>
    </div>

    <!-- Pulse -->
    <div v-if="pulse" class="flex-shrink-0">
      <span class="relative flex h-2.5 w-2.5">
        <span class="absolute inline-flex h-full w-full animate-ping rounded-full bg-primary opacity-50"></span>
        <span class="relative inline-flex h-2.5 w-2.5 rounded-full bg-primary"></span>
      </span>
    </div>
  </div>
</template>

<style scoped>
.kpi-card {
  transition: border-color 0.2s ease;
}
.kpi-card:hover {
  border-color: oklch(50% 0 0 / 0.3);
}
</style>

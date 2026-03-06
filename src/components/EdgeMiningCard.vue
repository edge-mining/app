<script setup lang="ts">
import type { Component } from "vue";

export interface CardStyleConfig {
  /** Hover gradient classes (e.g., "hover:from-amber-500/20 hover:to-orange-500/10") */
  gradient?: string;
  /** Icon color class (e.g., "text-amber-400") */
  iconColor?: string;
  /** Icon background color class (e.g., "bg-amber-500/20") */
  iconBgColor?: string;
  /** Accent border color class (e.g., "border-l-amber-500") */
  accentBorder?: string;
  /** Badge class (e.g., "badge-warning") */
  badgeClass?: string;
}

const props = withDefaults(
  defineProps<{
    /** Main icon component to display */
    icon?: Component;
    /** Icon size in pixels */
    iconSize?: number;
    /** Style configuration for colors and gradients */
    styleConfig?: CardStyleConfig;
    /** Whether to show opacity reduction (e.g., for inactive items) */
    dimmed?: boolean;
    /** Whether to show the icon pulse animation */
    pulse?: boolean;
    /** Custom card classes to append */
    cardClass?: string;
  }>(),
  {
    iconSize: 28,
    dimmed: false,
    pulse: false,
  }
);

// Default style config
const defaultStyleConfig: CardStyleConfig = {
  gradient: "hover:from-slate-500/20 hover:to-gray-500/10",
  iconColor: "text-slate-400",
  iconBgColor: "bg-base-100/60",
  accentBorder: "border-l-base-300/50 hover:border-l-slate-500",
  badgeClass: "badge-neutral",
};

// Merge provided style config with defaults
const mergedStyle = computed(() => ({
  ...defaultStyleConfig,
  ...props.styleConfig,
}));

import { computed } from "vue";
</script>

<template>
  <div
    class="edge-mining-card group relative flex flex-col rounded-xl border border-base-300/50 bg-gradient-to-br from-transparent to-transparent transition-all duration-300 hover:border-base-300 hover:shadow-lg hover:shadow-black/20"
    :class="[
      mergedStyle.gradient,
      `border-l-4 ${mergedStyle.accentBorder}`,
      { 'opacity-50': dimmed },
      cardClass,
    ]"
  >
    <!-- Header -->
    <div class="flex items-start justify-between p-4 pb-3">
      <div class="flex items-center gap-3">
        <!-- Icon Container -->
        <div
          class="relative flex h-12 w-12 items-center justify-center rounded-xl backdrop-blur-sm"
          :class="mergedStyle.iconBgColor"
        >
          <slot name="icon">
            <component
              v-if="icon"
              :is="icon"
              :size="iconSize"
              weight="duotone"
              :class="mergedStyle.iconColor"
            />
          </slot>
          <!-- Optional pulse indicator -->
          <span v-if="pulse" class="absolute -top-1 -right-1 h-3 w-3">
            <span
              class="absolute inline-flex h-full w-full animate-ping rounded-full opacity-75"
              :class="mergedStyle.iconColor?.replace('text-', 'bg-')"
            ></span>
            <span
              class="relative inline-flex h-3 w-3 rounded-full"
              :class="mergedStyle.iconColor?.replace('text-', 'bg-')?.replace('-400', '-500')"
            ></span>
          </span>
        </div>

        <!-- Title Area -->
        <div class="min-w-0">
          <slot name="title">
            <h3 class="text-lg font-semibold text-base-content leading-tight truncate">
              <!-- Title content via slot -->
            </h3>
          </slot>
          <div class="flex items-center gap-2 mt-1 flex-wrap">
            <slot name="badges"></slot>
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div class="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
        <slot name="actions"></slot>
      </div>
    </div>

    <!-- Main Content -->
    <div class="px-4 pb-4 flex-grow content-start">
      <slot></slot>
    </div>

    <!-- Footer -->
    <div v-if="$slots.footer" class="border-t border-base-300/30 px-4 py-3 bg-base-100/20 mt-auto">
      <slot name="footer"></slot>
    </div>
  </div>
</template>

<style scoped>
.edge-mining-card {
  background-color: oklch(28% 0 0 / 0.8);
}
</style>

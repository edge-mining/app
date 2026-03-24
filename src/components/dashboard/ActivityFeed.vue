<script setup lang="ts">
import type { DashboardEvent } from "../../core/composables/useDashboardPolling";
import {
  PhPlay,
  PhStop,
  PhArrowsClockwise,
  PhShieldCheck,
} from "@phosphor-icons/vue";

defineProps<{
  events: DashboardEvent[];
}>();

function eventIcon(type: DashboardEvent["type"]) {
  switch (type) {
    case "miner_start": return PhPlay;
    case "miner_stop": return PhStop;
    case "status_change": return PhArrowsClockwise;
    case "rule_triggered": return PhShieldCheck;
  }
}

function eventColor(type: DashboardEvent["type"]): string {
  switch (type) {
    case "miner_start": return "text-emerald-400";
    case "miner_stop": return "text-red-400";
    case "status_change": return "text-amber-400";
    case "rule_triggered": return "text-primary";
  }
}

function eventBg(type: DashboardEvent["type"]): string {
  switch (type) {
    case "miner_start": return "bg-emerald-500/15";
    case "miner_stop": return "bg-red-500/15";
    case "status_change": return "bg-amber-500/15";
    case "rule_triggered": return "bg-primary/15";
  }
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}
</script>

<template>
  <div class="space-y-1.5">
    <TransitionGroup name="event-list">
      <div
        v-for="event in events"
        :key="event.id"
        class="flex items-center gap-2.5 px-3 py-2 rounded-lg border border-base-300/10 bg-base-100/20"
      >
        <div
          class="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-lg"
          :class="eventBg(event.type)"
        >
          <component :is="eventIcon(event.type)" :size="14" :class="eventColor(event.type)" />
        </div>
        <div class="flex-1 min-w-0">
          <span class="text-sm text-base-content/80 truncate block">{{ event.message }}</span>
        </div>
        <span class="text-[10px] font-mono text-base-content/30 flex-shrink-0">
          {{ formatTime(event.timestamp) }}
        </span>
      </div>
    </TransitionGroup>

    <div v-if="events.length === 0" class="text-center py-8 text-base-content/30 text-sm">
      No events yet — monitoring for changes...
    </div>
  </div>
</template>

<style scoped>
.event-list-enter-active {
  transition: all 0.3s ease-out;
}
.event-list-leave-active {
  transition: all 0.2s ease-in;
}
.event-list-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}
.event-list-leave-to {
  opacity: 0;
  transform: translateX(20px);
}
.event-list-move {
  transition: transform 0.3s ease;
}
</style>

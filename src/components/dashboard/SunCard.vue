<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from "vue";
import { PhSun, PhSunHorizon } from "@phosphor-icons/vue";
import type { DecisionalContext } from "../../core/models/policy";

interface Props {
  latestDecisionalContexts: Map<string, DecisionalContext>;
}

const props = defineProps<Props>();

// Time tracking for reactive updates
const now = ref(Date.now());
let tickTimer: ReturnType<typeof setInterval> | undefined;
onMounted(() => { tickTimer = setInterval(() => { now.value = Date.now(); }, 1000); });
onUnmounted(() => { if (tickTimer) clearInterval(tickTimer); });

// Sun data from latest decisional contexts
const latestSun = computed(() => {
  for (const ctx of props.latestDecisionalContexts.values()) {
    if (ctx.sun) return ctx.sun;
  }
  return null;
});

const sunInfo = computed(() => {
  const sun = latestSun.value;
  if (!sun) return null;
  const nowMs = now.value;
  const sunrise = new Date(sun.sunrise).getTime();
  const sunset = new Date(sun.sunset).getTime();
  const isDay = nowMs >= sunrise && nowMs < sunset;
  return {
    sunriseTime: new Date(sun.sunrise).toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' }),
    sunsetTime: new Date(sun.sunset).toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' }),
    dawnTime: new Date(sun.dawn).toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' }),
    duskTime: new Date(sun.dusk).toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' }),
    daylightHours: (sun.daylight / 3600).toFixed(1),
    isDay,
    timeToSunrise: sunrise - nowMs,
    timeToSunset: sunset - nowMs,
    elevation: sun.elevation,
  };
});

function formatDuration(ms: number): string {
  const totalSec = Math.abs(Math.floor(ms / 1000));
  const h = Math.floor(totalSec / 3600);
  const m = Math.floor((totalSec % 3600) / 60);
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}

const sunArcProgress = computed(() => {
  if (!sunInfo.value) return 0.5;
  const sun = sunInfo.value;
  // Calculate progress along the sun's arc over 24-hour cycle
  // -1 to 0: before sunrise (approaching from left)
  // 0 to 1: from sunrise to sunset
  // 1+: after sunset (moving to right)
  const dayDuration = sun.timeToSunset - sun.timeToSunrise;
  const progress = -sun.timeToSunrise / dayDuration;
  // Clamp to visible range: -0.2 to 1.2 to show sun before/after arc
  return Math.max(-0.2, Math.min(1.2, progress));
});
</script>

<template>
  <div>
    <div class="flex items-center gap-2 mb-3">
      <PhSunHorizon :size="16" class="text-base-content/40" />
      <h2 class="text-sm font-semibold text-base-content/60 uppercase tracking-wider">
        Sun
      </h2>
    </div>
    <div v-if="sunInfo" class="relative rounded-xl overflow-hidden border border-base-300/20 backdrop-blur-sm p-5 bg-base-100/30">
      <!-- Sun position arc -->
      <div class="flex flex-col items-center gap-4">
        <!-- Visual sun position indicator -->
        <div class="w-full flex justify-center">
          <div class="relative w-32 h-24">
            <!-- Arc background -->
            <svg class="absolute inset-0 w-full h-full" viewBox="0 0 120 60" preserveAspectRatio="xMidYMid meet">
              <path d="M 10 55 Q 60 15 110 55" stroke="currentColor" stroke-width="1.5" fill="none" class="text-base-content/10"/>
            </svg>
            <!-- Sun position marker -->
            <div class="absolute inset-0 flex items-end justify-center pb-1">
              <div class="relative w-full h-full flex items-end justify-center">
                <div
                  class="absolute transition-all duration-1000"
                  :style="{
                    left: `${sunArcProgress * 100}%`,
                    bottom: `${Math.sin(Math.PI * sunArcProgress) * 35}%`,
                    transform: 'translateX(-50%)'
                  }"
                >
                  <div :class="sunInfo.isDay ? 'text-yellow-400 drop-shadow-lg' : 'text-slate-400 drop-shadow-lg'">
                    <PhSun :size="28" weight="fill" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Day/Night status badge -->
        <div class="w-full flex justify-center">
          <div :class="[
            'px-3 py-1.5 rounded-full text-xs font-semibold flex items-center gap-2',
            sunInfo.isDay
              ? 'bg-yellow-400/20 text-yellow-500 border border-yellow-400/30'
              : 'bg-slate-600/20 text-slate-300 border border-slate-600/30'
          ]">
            <div :class="[
              'w-2 h-2 rounded-full',
              sunInfo.isDay ? 'bg-yellow-400 animate-pulse' : 'bg-slate-400'
            ]" />
            {{ sunInfo.isDay ? 'Daytime' : 'Nighttime' }}
          </div>
        </div>

        <!-- Sunrise / Sunset row -->
        <div class="grid grid-cols-2 gap-3 w-full">
          <div class="rounded-lg bg-base-content/5 border border-base-content/10 p-4 flex flex-col items-center gap-3">
            <span class="text-[10px] text-base-content/40 uppercase tracking-wider font-medium">Sunrise</span>
            <div class="relative">
              <PhSun :size="40" class="text-yellow-400" weight="fill" />
              <div class="absolute inset-0 animate-pulse text-yellow-400 opacity-20">
                <PhSun :size="40" weight="fill" />
              </div>
            </div>
            <div class="flex flex-col items-center gap-1">
              <span class="text-sm font-bold text-base-content/90">{{ sunInfo.sunriseTime }}</span>
              <span v-if="sunInfo.timeToSunrise > 0" class="text-[10px] text-yellow-500 font-medium">
                in {{ formatDuration(sunInfo.timeToSunrise) }}
              </span>
              <span v-else class="text-[10px] text-base-content/40 font-medium">
                {{ formatDuration(sunInfo.timeToSunrise) }} ago
              </span>
            </div>
          </div>
          <div class="rounded-lg bg-base-content/5 border border-base-content/10 p-4 flex flex-col items-center gap-3">
            <span class="text-[10px] text-base-content/40 uppercase tracking-wider font-medium">Sunset</span>
            <div class="relative">
              <PhSunHorizon :size="40" class="text-orange-400" weight="fill" />
              <div class="absolute inset-0 animate-pulse text-orange-400 opacity-20">
                <PhSunHorizon :size="40" weight="fill" />
              </div>
            </div>
            <div class="flex flex-col items-center gap-1">
              <span class="text-sm font-bold text-base-content/90">{{ sunInfo.sunsetTime }}</span>
              <span v-if="sunInfo.timeToSunset > 0" class="text-[10px] text-orange-500 font-medium">
                in {{ formatDuration(sunInfo.timeToSunset) }}
              </span>
              <span v-else class="text-[10px] text-base-content/40 font-medium">
                {{ formatDuration(sunInfo.timeToSunset) }} ago
              </span>
            </div>
          </div>
        </div>

        <!-- Extra info row -->
        <div class="w-full flex items-center justify-between px-2 py-2 rounded-lg bg-base-content/5 border border-base-content/10">
          <div class="flex flex-col items-center gap-0.5">
            <span class="text-xs text-base-content/40 uppercase tracking-wider">Daylight</span>
            <span class="text-sm font-bold text-base-content/80">{{ sunInfo.daylightHours }}h</span>
          </div>
          <div class="h-8 w-px bg-base-content/10" />
          <div class="flex flex-col items-center gap-0.5">
            <span class="text-xs text-base-content/40 uppercase tracking-wider">Elevation</span>
            <span v-if="sunInfo.elevation != null" class="text-sm font-bold text-base-content/80">{{ sunInfo.elevation.toFixed(1) }}°</span>
            <span v-else class="text-sm text-base-content/40">N/A</span>
          </div>
        </div>
      </div>
    </div>
    <div v-else class="rounded-xl border border-base-300/20 bg-base-100/30 backdrop-blur-sm p-4 flex flex-col items-center justify-center py-6 text-center">
      <PhSunHorizon :size="28" class="text-base-content/15 mb-2" />
      <span class="text-sm text-base-content/30">No sun data</span>
    </div>
  </div>
</template>

<style scoped></style>

<script setup lang="ts">
import { computed } from "vue";
import {
  PhUsersFour,
  PhCheckCircle,
  PhWarningCircle,
  PhXCircle,
  PhCpu,
} from "@phosphor-icons/vue";
import type { MiningPerformanceSnapshot } from "../../core/models/policy";
import { normalizeHashRate } from "../../core/utils/index";
import { formatTimeAgo } from "../../core/utils/index";

const props = defineProps<{
  snapshot: MiningPerformanceSnapshot;
}>();

function formatHashRate(value?: number | null, unit?: string | null): string {
  if (value == null) return "-";
  const th = normalizeHashRate(value, unit || "TH/s");
  if (th >= 1000) return `${(th / 1000).toFixed(2)} PH/s`;
  if (th >= 1) return `${th.toFixed(1)} TH/s`;
  if (th >= 0.001) return `${(th * 1000).toFixed(0)} GH/s`;
  return `${(th * 1_000_000).toFixed(0)} MH/s`;
}

const pool = computed(() => props.snapshot.pool_stats);
const workers = computed(() => pool.value?.workers || []);
</script>

<template>
  <div class="rounded-xl border border-base-300/20 bg-base-100/30 backdrop-blur-sm overflow-hidden">
    <div class="flex items-center justify-between px-4 py-3 border-b border-base-300/10">
      <div class="flex items-center gap-2">
        <PhUsersFour :size="16" class="text-sky-400" />
        <span class="text-sm font-medium text-base-content/70">Pool Stats</span>
      </div>
      <span v-if="pool" class="text-[10px] text-base-content/30">
        {{ formatTimeAgo(pool.timestamp) }}
      </span>
    </div>

    <div v-if="!pool" class="p-6 text-center text-sm text-base-content/30">
      Pool stats not available.
    </div>

    <div v-else class="p-4 space-y-4">
      <!-- Hashrate trio -->
      <div class="grid grid-cols-3 gap-3">
        <div class="rounded-lg bg-base-content/5 border border-base-content/10 px-3 py-2">
          <div class="text-[10px] uppercase tracking-wider text-base-content/40 mb-1">
            Current
          </div>
          <div class="text-lg font-bold tabular-nums text-primary">
            {{ formatHashRate(pool.current_hashrate?.value, pool.current_hashrate?.unit) }}
          </div>
        </div>
        <div class="rounded-lg bg-base-content/5 border border-base-content/10 px-3 py-2">
          <div class="text-[10px] uppercase tracking-wider text-base-content/40 mb-1">
            Avg 24h
          </div>
          <div class="text-lg font-bold tabular-nums text-base-content/80">
            {{ formatHashRate(pool.average_hashrate_24h?.value, pool.average_hashrate_24h?.unit) }}
          </div>
        </div>
        <div class="rounded-lg bg-base-content/5 border border-base-content/10 px-3 py-2">
          <div class="text-[10px] uppercase tracking-wider text-base-content/40 mb-1">
            Avg 7d
          </div>
          <div class="text-lg font-bold tabular-nums text-base-content/80">
            {{ formatHashRate(pool.average_hashrate_7d?.value, pool.average_hashrate_7d?.unit) }}
          </div>
        </div>
      </div>

      <!-- Workers list -->
      <div>
        <div class="flex items-center justify-between mb-2">
          <span class="text-[11px] uppercase tracking-wider text-base-content/40">
            Workers
          </span>
          <span class="text-[10px] text-base-content/30">
            {{ workers.length }} reporting
          </span>
        </div>

        <div v-if="workers.length === 0" class="text-center py-4 text-sm text-base-content/30">
          No workers reported by the pool.
        </div>

        <div v-else class="space-y-1.5 max-h-[280px] overflow-y-auto">
          <div
            v-for="(w, i) in workers"
            :key="`${w.worker_name}-${i}`"
            class="flex items-center gap-2 px-2 py-2 rounded-lg border border-base-300/10 bg-base-100/20 text-xs"
          >
            <PhCpu :size="14" class="text-base-content/50 shrink-0" />
            <span class="font-medium text-base-content/80 truncate flex-1 min-w-0">
              {{ w.worker_name }}
            </span>
            <span class="font-mono tabular-nums text-emerald-400 shrink-0">
              {{ formatHashRate(w.hashrate?.value, w.hashrate?.unit) }}
            </span>
            <div class="flex items-center gap-2 text-base-content/50 shrink-0">
              <span
                v-if="w.valid_shares != null"
                class="flex items-center gap-1"
                :title="`Valid shares: ${w.valid_shares}`"
              >
                <PhCheckCircle :size="12" class="text-emerald-400/70" />
                {{ w.valid_shares }}
              </span>
              <span
                v-if="w.stale_shares != null"
                class="flex items-center gap-1"
                :title="`Stale shares: ${w.stale_shares}`"
              >
                <PhWarningCircle :size="12" class="text-amber-400/70" />
                {{ w.stale_shares }}
              </span>
              <span
                v-if="w.rejected_shares != null"
                class="flex items-center gap-1"
                :title="`Rejected shares: ${w.rejected_shares}`"
              >
                <PhXCircle :size="12" class="text-red-400/70" />
                {{ w.rejected_shares }}
              </span>
            </div>
            <span
              v-if="w.last_share_at"
              class="text-[10px] text-base-content/30 tabular-nums shrink-0"
              :title="`Last share at ${w.last_share_at}`"
            >
              {{ formatTimeAgo(w.last_share_at) }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped></style>

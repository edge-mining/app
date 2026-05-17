<script setup lang="ts">
import { computed } from "vue";
import { PhCurrencyBtc, PhClockCountdown, PhCalendar } from "@phosphor-icons/vue";
import type { MiningPerformanceSnapshot } from "../../core/models/policy";
import { formatTimeAgo } from "../../core/utils/index";

const props = defineProps<{
  snapshot: MiningPerformanceSnapshot;
}>();

const pool = computed(() => props.snapshot.pool_stats);
const schedule = computed(() => props.snapshot.payout_schedule);

function formatSats(sats: number | null | undefined): string {
  if (sats == null) return "-";
  if (Math.abs(sats) >= 100_000_000) {
    return `${(sats / 100_000_000).toFixed(4)} BTC`;
  }
  return `${sats.toLocaleString()} sat`;
}

function formatFrequency(f?: string | null): string {
  if (!f) return "-";
  return f.charAt(0).toUpperCase() + f.slice(1).toLowerCase();
}
</script>

<template>
  <div class="rounded-xl border border-base-300/20 bg-base-100/30 backdrop-blur-sm overflow-hidden">
    <div class="flex items-center justify-between px-4 py-3 border-b border-base-300/10">
      <div class="flex items-center gap-2">
        <PhCurrencyBtc :size="16" class="text-yellow-400" />
        <span class="text-sm font-medium text-base-content/70">Payout</span>
      </div>
    </div>

    <div class="p-4 space-y-3">
      <div class="rounded-lg bg-base-content/5 border border-base-content/10 px-3 py-2">
        <div class="text-[10px] uppercase tracking-wider text-base-content/40 mb-1">
          Unpaid Balance
        </div>
        <div class="text-xl font-bold tabular-nums text-yellow-400">
          {{ formatSats(pool?.unpaid_balance) }}
        </div>
      </div>

      <div class="rounded-lg bg-base-content/5 border border-base-content/10 px-3 py-2">
        <div class="text-[10px] uppercase tracking-wider text-base-content/40 mb-1">
          Estimated Next Payout
        </div>
        <div class="text-base font-bold tabular-nums text-base-content/80">
          {{ formatSats(pool?.estimated_next_payout) }}
        </div>
      </div>

      <div class="grid grid-cols-2 gap-2">
        <div class="rounded-lg bg-base-content/5 border border-base-content/10 px-3 py-2">
          <div class="text-[10px] uppercase tracking-wider text-base-content/40 mb-1 flex items-center gap-1">
            <PhCalendar :size="11" />
            Frequency
          </div>
          <div class="text-sm font-semibold text-base-content/80">
            {{ formatFrequency(schedule?.frequency) }}
          </div>
        </div>
        <div class="rounded-lg bg-base-content/5 border border-base-content/10 px-3 py-2">
          <div class="text-[10px] uppercase tracking-wider text-base-content/40 mb-1">
            Threshold
          </div>
          <div class="text-sm font-semibold text-base-content/80">
            {{ formatSats(schedule?.threshold) }}
          </div>
        </div>
      </div>

      <div class="rounded-lg bg-base-content/5 border border-base-content/10 px-3 py-2 flex items-center gap-2">
        <PhClockCountdown :size="14" class="text-teal-400" />
        <div class="flex-1 min-w-0">
          <div class="text-[10px] uppercase tracking-wider text-base-content/40">
            Next Payout
          </div>
          <div class="text-sm font-semibold text-base-content/80 truncate">
            <template v-if="schedule?.next_payout_at">
              {{ new Date(schedule.next_payout_at).toLocaleString() }}
              <span class="text-base-content/40 text-xs ml-1">
                ({{ formatTimeAgo(schedule.next_payout_at) }})
              </span>
            </template>
            <template v-else>-</template>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped></style>

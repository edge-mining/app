<script setup lang="ts">
import type { OptimizationPolicy } from "../../core/models/policy";
import { computed, ref } from "vue";
import {
  PhPencil,
  PhTrash,
  PhPlay,
  PhStop,
  PhShieldCheck,
  PhListChecks,
  PhUser,
  PhCalendarBlank,
  PhGitBranch,
} from "@phosphor-icons/vue";
import ConfirmDialog from "../ConfirmDialog.vue";
import ResourceId from "../ResourceId.vue";
import { formatDate } from "../../core/utils/index";

const props = defineProps<{
  policy: OptimizationPolicy;
}>();

const emit = defineEmits<{
  edit: [policy: OptimizationPolicy];
  delete: [policy: OptimizationPolicy];
  manageRules: [policy: OptimizationPolicy];
  check: [policy: OptimizationPolicy];
}>();

const showDeleteConfirm = ref(false);

// Summarise rules
const startRulesCount = computed(() => props.policy.start_rules?.length ?? 0);
const stopRulesCount = computed(() => props.policy.stop_rules?.length ?? 0);
const totalRulesCount = computed(() => startRulesCount.value + stopRulesCount.value);

const enabledStartRules = computed(
  () => props.policy.start_rules?.filter((r) => r.enabled).length ?? 0
);
const enabledStopRules = computed(
  () => props.policy.stop_rules?.filter((r) => r.enabled).length ?? 0
);

// Health indicator based on rule balance
const healthStatus = computed(() => {
  if (totalRulesCount.value === 0) return "empty";
  if (startRulesCount.value === 0) return "no-start";
  if (stopRulesCount.value === 0) return "no-stop";
  if (enabledStartRules.value === 0 && enabledStopRules.value === 0)
    return "all-disabled";
  return "ok";
});

const healthConfig = computed(() => {
  const configs: Record<string, { label: string; color: string; dotColor: string }> = {
    ok: { label: "Balanced", color: "text-primary", dotColor: "bg-primary" },
    empty: { label: "No rules", color: "text-base-content/40", dotColor: "bg-base-content/30" },
    "no-start": { label: "Missing start rules", color: "text-amber-400", dotColor: "bg-amber-400" },
    "no-stop": { label: "Missing stop rules", color: "text-amber-400", dotColor: "bg-amber-400" },
    "all-disabled": { label: "All rules disabled", color: "text-rose-300", dotColor: "bg-rose-300" },
  };
  return configs[healthStatus.value] || configs["empty"];
});

function handleEdit() {
  emit("edit", props.policy);
}

function handleDeleteClick() {
  showDeleteConfirm.value = true;
}

function confirmDelete() {
  showDeleteConfirm.value = false;
  emit("delete", props.policy);
}

function cancelDelete() {
  showDeleteConfirm.value = false;
}

function handleManageRules() {
  emit("manageRules", props.policy);
}

function handleCheck() {
  emit("check", props.policy);
}
</script>

<template>
  <div
    class="policy-card group relative flex flex-col rounded-xl border border-base-300/50 bg-gradient-to-br from-transparent to-transparent transition-all duration-300 hover:border-base-300 hover:shadow-lg hover:shadow-black/20 hover:from-indigo-500/10 hover:to-violet-500/5 border-l-4 border-l-base-300/50 hover:border-l-indigo-500"
  >
    <!-- Header -->
    <div class="flex items-start justify-between p-4 pb-2">
      <div class="flex items-center gap-3 min-w-0">
        <!-- Icon -->
        <div
          class="relative flex h-12 w-12 items-center justify-center rounded-xl bg-base-100/60 backdrop-blur-sm flex-shrink-0"
        >
          <PhGitBranch :size="28" weight="duotone" class="text-indigo-400" />
          <!-- Health dot -->
          <span class="absolute -top-1 -right-1 flex h-3 w-3">
            <span
              v-if="healthStatus === 'ok'"
              class="absolute inline-flex h-full w-full animate-ping rounded-full bg-primary opacity-75"
            ></span>
            <span
              class="relative inline-flex h-3 w-3 rounded-full border-2 border-base-100"
              :class="healthConfig.dotColor"
            ></span>
          </span>
        </div>

        <!-- Title + badges -->
        <div class="min-w-0">
          <h3 class="text-lg font-semibold text-base-content leading-tight truncate">
            {{ policy.name }}
          </h3>
          <div class="flex items-center gap-2 mt-1 flex-wrap">
            <!-- Version badge -->
            <span
              v-if="policy.metadata?.version"
              class="badge badge-sm bg-indigo-500/20 text-indigo-400 border-0"
            >
              v{{ policy.metadata.version }}
            </span>
            <!-- Health badge -->
            <span class="text-[11px]" :class="healthConfig.color">
              {{ healthConfig.label }}
            </span>
            <ResourceId v-if="policy.id" :id="policy.id" />
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div class="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
        <button
          class="btn btn-ghost btn-sm btn-square hover:bg-success/20"
          title="Check policy validity"
          @click="handleCheck"
        >
          <PhShieldCheck :size="18" class="text-success" />
        </button>
        <button
          class="btn btn-ghost btn-sm btn-square hover:bg-primary/20"
          title="Edit policy"
          @click="handleEdit"
        >
          <PhPencil :size="18" class="text-primary" />
        </button>
        <button
          class="btn btn-ghost btn-sm btn-square hover:bg-error/20"
          title="Delete policy"
          @click="handleDeleteClick"
        >
          <PhTrash :size="18" class="text-error" />
        </button>
      </div>
    </div>

    <!-- Description -->
    <div class="px-4 pb-3">
      <p
        v-if="policy.description"
        class="text-sm text-base-content/60 line-clamp-2"
      >
        {{ policy.description }}
      </p>
      <p v-else class="text-sm text-base-content/30 italic">No description</p>
    </div>

    <!-- Rules Summary -->
    <div class="px-4 pb-3 flex-grow">
      <div class="grid grid-cols-2 gap-2">
        <!-- Start Rules -->
        <button
          class="flex flex-col items-center gap-1 rounded-lg bg-primary/10 border border-primary/20 p-3 hover:bg-primary/20 transition-colors cursor-pointer"
          @click="handleManageRules"
          title="Manage start rules"
        >
          <div class="flex items-center gap-1.5">
            <PhPlay :size="16" class="text-primary" weight="fill" />
            <span class="text-2xl font-bold text-primary">{{ startRulesCount }}</span>
          </div>
          <span class="text-[11px] text-primary/70 uppercase tracking-wider font-medium">
            Start Rules
          </span>
          <span
            v-if="startRulesCount > 0"
            class="text-[10px] text-base-content/40"
          >
            {{ enabledStartRules }}/{{ startRulesCount }} enabled
          </span>
        </button>

        <!-- Stop Rules -->
        <button
          class="flex flex-col items-center gap-1 rounded-lg bg-rose-300/10 border border-rose-300/20 p-3 hover:bg-rose-300/20 transition-colors cursor-pointer"
          @click="handleManageRules"
          title="Manage stop rules"
        >
          <div class="flex items-center gap-1.5">
            <PhStop :size="16" class="text-rose-300" weight="fill" />
            <span class="text-2xl font-bold text-rose-300">{{ stopRulesCount }}</span>
          </div>
          <span class="text-[11px] text-rose-300/70 uppercase tracking-wider font-medium">
            Stop Rules
          </span>
          <span
            v-if="stopRulesCount > 0"
            class="text-[10px] text-base-content/40"
          >
            {{ enabledStopRules }}/{{ stopRulesCount }} enabled
          </span>
        </button>
      </div>

      <!-- Manage Rules CTA -->
      <button
        class="btn btn-sm btn-outline btn-secondary gap-2 w-full mt-3"
        @click="handleManageRules"
      >
        <PhListChecks :size="16" />
        Manage Rules
      </button>
    </div>

    <!-- Footer -->
    <div class="border-t border-base-300/30 px-4 py-3 bg-base-100/20 mt-auto">
      <div class="flex items-center justify-between gap-2 text-xs text-base-content/40">
        <!-- Author -->
        <div v-if="policy.metadata?.author" class="flex items-center gap-1.5 min-w-0">
          <PhUser :size="13" class="flex-shrink-0" />
          <span class="truncate">{{ policy.metadata.author }}</span>
        </div>
        <div v-else></div>

        <!-- Last modified -->
        <div v-if="policy.metadata?.last_modified" class="flex items-center gap-1.5 flex-shrink-0">
          <PhCalendarBlank :size="13" />
          <span>{{ formatDate(policy.metadata.last_modified) }}</span>
        </div>
      </div>
    </div>
  </div>

  <!-- Delete Confirmation Dialog -->
  <ConfirmDialog
    :open="showDeleteConfirm"
    title="Delete Policy"
    :message="`Are you sure you want to delete policy '${policy.name}'? All associated rules will also be deleted.`"
    confirm-text="Delete"
    variant="danger"
    @confirm="confirmDelete"
    @cancel="cancelDelete"
  />
</template>

<style scoped>
.policy-card {
  background-color: oklch(28% 0 0 / 0.8);
}
</style>

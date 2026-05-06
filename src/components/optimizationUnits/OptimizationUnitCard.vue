<script setup lang="ts">
import type { OptimizationUnit } from "../../core/models/optimizationUnit";
import { usePolicyStore } from "../../core/stores/policyStore";
import { useMinerStore } from "../../core/stores/minerStore";
import { useEnergySourceStore } from "../../core/stores/energySourceStore";
import { useHomeLoadsProfileStore } from "../../core/stores/homeLoadsProfileStore";
import { useNotifierStore } from "../../core/stores/notifierStore";
import { computed, ref } from "vue";
import {
  PhPencil,
  PhTrash,
  PhGraph,
  PhCpu,
  PhLightning,
  PhChartLine,
  PhBell,
  PhShieldCheck,
  PhToggleLeft,
  PhToggleRight,
} from "@phosphor-icons/vue";
import ConfirmDialog from "../ConfirmDialog.vue";
import EdgeMiningCard, { type CardStyleConfig } from "../EdgeMiningCard.vue";
import ResourceId from "../ResourceId.vue";

const props = defineProps<{
  unit: OptimizationUnit;
}>();

const emit = defineEmits<{
  edit: [unit: OptimizationUnit];
  delete: [unit: OptimizationUnit];
  toggleEnabled: [unit: OptimizationUnit];
}>();

const policyStore = usePolicyStore();
const minerStore = useMinerStore();
const energySourceStore = useEnergySourceStore();
const homeLoadsProfileStore = useHomeLoadsProfileStore();
const notifierStore = useNotifierStore();
const showDeleteConfirm = ref(false);

// Resolved references
const policy = computed(() => {
  if (!props.unit.policy_id) return null;
  return policyStore.policies.find((p) => p.id?.toString() === props.unit.policy_id);
});

const energySource = computed(() => {
  if (!props.unit.energy_source_id) return null;
  return energySourceStore.energySources.find(
    (es) => es.id?.toString() === props.unit.energy_source_id
  );
});

const homeLoadsProfile = computed(() => {
  if (!props.unit.home_loads_profile_id) return null;
  return homeLoadsProfileStore.profiles.find(
    (p) => p.id?.toString() === props.unit.home_loads_profile_id
  );
});

const assignedMiners = computed(() => {
  return minerStore.miners.filter((m) =>
    props.unit.target_miner_ids.includes(m.id!.toString())
  );
});

const assignedNotifiers = computed(() => {
  return notifierStore.notifiers.filter((n) =>
    props.unit.notifier_ids.includes(n.id!.toString())
  );
});

// Card styling based on enabled state
const styleConfig = computed<CardStyleConfig>(() => {
  if (props.unit.is_enabled) {
    return {
      gradient: "hover:from-teal-500/20 hover:to-emerald-500/10",
      iconColor: "text-teal-400",
      iconBgColor: "bg-teal-500/20",
      accentBorder: "border-l-base-300/50 hover:border-l-teal-500",
      badgeClass: "badge-success",
    };
  }
  return {
    gradient: "hover:from-slate-500/20 hover:to-gray-500/10",
    iconColor: "text-slate-400",
    iconBgColor: "bg-slate-500/20",
    accentBorder: "border-l-base-300/50 hover:border-l-slate-500",
    badgeClass: "badge-ghost",
  };
});

// Assignment count for summary
const totalAssignments = computed(() => {
  let count = 0;
  if (props.unit.policy_id) count++;
  if (props.unit.energy_source_id) count++;
  if (props.unit.home_loads_profile_id) count++;
  count += props.unit.target_miner_ids.length;
  count += props.unit.notifier_ids.length;
  return count;
});

function handleEdit() {
  emit("edit", props.unit);
}

function handleDeleteClick() {
  showDeleteConfirm.value = true;
}

function confirmDelete() {
  showDeleteConfirm.value = false;
  emit("delete", props.unit);
}

function cancelDelete() {
  showDeleteConfirm.value = false;
}

function handleToggleEnabled() {
  emit("toggleEnabled", props.unit);
}
</script>

<template>
  <EdgeMiningCard
    :icon="PhGraph"
    :icon-size="26"
    :style-config="styleConfig"
    :dimmed="!unit.is_enabled"
    :pulse="unit.is_enabled"
    card-class="min-h-[220px]"
  >
    <!-- Title -->
    <template #title>
      {{ unit.name || "Unnamed Unit" }}
    </template>

    <!-- Badges -->
    <template #badges>
      <!-- Enabled Status Badge -->
      <span class="badge badge-sm" :class="unit.is_enabled ? 'badge-success' : 'badge-ghost'">
        {{ unit.is_enabled ? "Enabled" : "Disabled" }}
      </span>
      <!-- Assignments count -->
      <span v-if="totalAssignments > 0" class="badge badge-sm badge-outline">
        {{ totalAssignments }} linked
      </span>
      <!-- ID -->
      <ResourceId v-if="unit.id" :id="unit.id" />
    </template>

    <!-- Actions -->
    <template #actions>
      <button
        class="btn btn-ghost btn-sm btn-square hover:bg-primary/20"
        title="Edit"
        @click="handleEdit"
      >
        <PhPencil :size="18" class="text-primary" />
      </button>
      <button
        class="btn btn-ghost btn-sm btn-square hover:bg-error/20"
        title="Delete"
        @click="handleDeleteClick"
      >
        <PhTrash :size="18" class="text-error" />
      </button>
    </template>

    <!-- Main Content -->
    <div class="space-y-3">
      <!-- Description -->
      <p v-if="unit.description" class="text-sm text-base-content/60 -mt-1 line-clamp-2">
        {{ unit.description }}
      </p>

      <!-- Miners Section -->
      <div class="metric-box bg-base-100/40 rounded-lg px-3 py-2">
        <div class="flex items-center justify-between mb-1.5">
          <div class="flex items-center gap-1.5 text-xs text-base-content/60">
            <PhCpu :size="14" />
            <span>Target Miners</span>
          </div>
          <span class="text-sm font-semibold text-base-content">
            {{ assignedMiners.length }}
          </span>
        </div>
        <div v-if="assignedMiners.length > 0" class="flex flex-wrap gap-1">
          <span
            v-for="miner in assignedMiners.slice(0, 3)"
            :key="miner.id"
            class="badge badge-xs badge-ghost"
          >
            {{ miner.name }}
          </span>
          <span v-if="assignedMiners.length > 3" class="badge badge-xs badge-ghost">
            +{{ assignedMiners.length - 3 }} more
          </span>
        </div>
        <div v-else class="text-xs text-base-content/30 italic">
          No miners assigned
        </div>
      </div>

      <!-- Notifiers Section -->
      <div class="metric-box bg-base-100/40 rounded-lg px-3 py-2">
        <div class="flex items-center justify-between mb-1.5">
          <div class="flex items-center gap-1.5 text-xs text-base-content/60">
            <PhBell :size="14" />
            <span>Notifiers</span>
          </div>
          <span class="text-sm font-semibold text-base-content">
            {{ assignedNotifiers.length }}
          </span>
        </div>
        <div v-if="assignedNotifiers.length > 0" class="flex flex-wrap gap-1">
          <span
            v-for="notifier in assignedNotifiers.slice(0, 3)"
            :key="notifier.id"
            class="badge badge-xs badge-ghost"
          >
            {{ notifier.name }}
          </span>
          <span v-if="assignedNotifiers.length > 3" class="badge badge-xs badge-ghost">
            +{{ assignedNotifiers.length - 3 }} more
          </span>
        </div>
        <div v-else class="text-xs text-base-content/30 italic">
          No notifiers assigned
        </div>
      </div>
    </div>

    <!-- Footer -->
    <template #footer>
      <div class="flex items-center justify-between gap-2">
        <!-- Left side: linked resources -->
        <div class="flex flex-wrap gap-3 min-w-0">
          <!-- Policy -->
          <div v-if="policy" class="flex items-center gap-1.5 min-w-0">
            <div class="h-6 w-6 rounded-full bg-primary/20 flex items-center justify-center flex-shrink-0">
              <PhShieldCheck :size="14" class="text-primary" />
            </div>
            <div class="min-w-0">
              <div class="text-[10px] uppercase tracking-wider text-base-content/40">Policy</div>
              <div class="text-sm text-base-content/80 leading-tight truncate max-w-[100px]">
                {{ policy.name }}
              </div>
            </div>
          </div>

          <!-- Energy Source -->
          <div v-if="energySource" class="flex items-center gap-1.5 min-w-0">
            <div class="h-6 w-6 rounded-full bg-amber-500/20 flex items-center justify-center flex-shrink-0">
              <PhLightning :size="14" class="text-amber-400" />
            </div>
            <div class="min-w-0">
              <div class="text-[10px] uppercase tracking-wider text-base-content/40">Energy</div>
              <div class="text-sm text-base-content/80 leading-tight truncate max-w-[100px]">
                {{ energySource.name }}
              </div>
            </div>
          </div>

          <!-- Home Loads Profile -->
          <div v-if="homeLoadsProfile" class="flex items-center gap-1.5 min-w-0">
            <div class="h-6 w-6 rounded-full bg-info/20 flex items-center justify-center flex-shrink-0">
              <PhChartLine :size="14" class="text-info" />
            </div>
            <div class="min-w-0">
              <div class="text-[10px] uppercase tracking-wider text-base-content/40">Home Loads</div>
              <div class="text-sm text-base-content/80 leading-tight truncate max-w-[100px]">
                {{ homeLoadsProfile.name }}
              </div>
            </div>
          </div>

          <!-- No assignments fallback -->
          <div
            v-if="!policy && !energySource && !homeLoadsProfile"
            class="text-xs text-base-content/40 italic flex items-center gap-1"
          >
            No resources linked
          </div>
        </div>

        <!-- Right side: Enable/Disable toggle -->
        <div class="flex-shrink-0">
          <button
            class="btn btn-xs gap-1"
            :class="unit.is_enabled ? 'btn-ghost' : 'btn-success'"
            @click="handleToggleEnabled"
            :title="unit.is_enabled ? 'Disable unit' : 'Enable unit'"
          >
            <component
              :is="unit.is_enabled ? PhToggleRight : PhToggleLeft"
              :size="16"
            />
            {{ unit.is_enabled ? "Disable" : "Enable" }}
          </button>
        </div>
      </div>
    </template>
  </EdgeMiningCard>

  <!-- Delete Confirmation Dialog -->
  <ConfirmDialog
    :open="showDeleteConfirm"
    title="Delete Optimization Unit"
    :message="`Are you sure you want to delete '${unit.name}'? This will remove all associated assignments.`"
    confirm-text="Delete"
    variant="danger"
    @confirm="confirmDelete"
    @cancel="cancelDelete"
  />
</template>

<style scoped>
.metric-box {
  backdrop-filter: blur(4px);
}
</style>

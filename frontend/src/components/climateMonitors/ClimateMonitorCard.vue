<script setup lang="ts">
import type { ClimateMonitor, ClimateMonitorAdapter } from "../../core/models/climateMonitor";
import { useExternalServiceStore } from "../../core/stores/externalServiceStore";
import { formatType } from "../../core/utils/index";
import { computed, ref } from "vue";
import {
  PhPencil,
  PhTrash,
  PhThermometerSimple,
  PhHouse,
  PhPlugs,
  PhLink,
  PhCheckCircle,
  PhWarningCircle,
} from "@phosphor-icons/vue";
import ConfirmDialog from "../ConfirmDialog.vue";
import EdgeMiningCard, { type CardStyleConfig } from "../EdgeMiningCard.vue";
import ResourceId from "../ResourceId.vue";

const props = defineProps<{
  climateMonitor: ClimateMonitor;
  assignedZonesCount?: number;
}>();

const emit = defineEmits<{
  edit: [monitor: ClimateMonitor];
  delete: [monitor: ClimateMonitor];
  check: [monitor: ClimateMonitor];
}>();

const externalServiceStore = useExternalServiceStore();
const showDeleteConfirm = ref(false);

// External service linked
const externalService = computed(() => {
  if (!props.climateMonitor.external_service_id) return null;
  return externalServiceStore.externalServices.find(
    (es) => es.id?.toString() === props.climateMonitor.external_service_id
  );
});

// Adapter type configuration for styling
const adapterConfig = computed(() => {
  const type = props.climateMonitor.adapter_type;

  const configs: Record<ClimateMonitorAdapter, { icon: typeof PhThermometerSimple; styleConfig: CardStyleConfig }> = {
    dummy: {
      icon: PhThermometerSimple,
      styleConfig: {
        gradient: "hover:from-emerald-500/20 hover:to-teal-500/10",
        iconColor: "text-emerald-400",
        badgeClass: "badge-success",
        accentBorder: "border-l-base-300/50 hover:border-l-emerald-500",
      },
    },
    home_assistant_api: {
      icon: PhHouse,
      styleConfig: {
        gradient: "hover:from-orange-500/20 hover:to-amber-500/10",
        iconColor: "text-orange-400",
        badgeClass: "badge-warning",
        accentBorder: "border-l-base-300/50 hover:border-l-orange-500",
      },
    },
  };

  return (
    configs[type] || {
      icon: PhThermometerSimple,
      styleConfig: {
        gradient: "hover:from-slate-500/20 hover:to-gray-500/10",
        iconColor: "text-slate-400",
        badgeClass: "bg-slate-500/20 text-slate-400",
        accentBorder: "border-l-base-300/50 hover:border-l-slate-500",
      },
    }
  );
});

function handleEdit() {
  emit("edit", props.climateMonitor);
}

function handleCheck() {
  emit("check", props.climateMonitor);
}

function handleDeleteClick() {
  showDeleteConfirm.value = true;
}

function confirmDelete() {
  showDeleteConfirm.value = false;
  emit("delete", props.climateMonitor);
}

function cancelDelete() {
  showDeleteConfirm.value = false;
}
</script>

<template>
  <EdgeMiningCard
    :icon="adapterConfig.icon"
    :style-config="adapterConfig.styleConfig"
    card-class="min-h-[220px]"
  >
    <!-- Title -->
    <template #title>
      {{ climateMonitor.name }}
    </template>

    <!-- Badges -->
    <template #badges>
      <span class="badge badge-sm max-w-[10rem] px-2 overflow-hidden" :class="adapterConfig.styleConfig.badgeClass" :title="formatType(climateMonitor.adapter_type)">
        <span class="marquee-on-overflow">{{ formatType(climateMonitor.adapter_type) }}</span>
      </span>
      <ResourceId v-if="climateMonitor.id" :id="climateMonitor.id" />
    </template>

    <!-- Actions -->
    <template #actions>
      <button
        class="btn btn-ghost btn-sm btn-square hover:bg-success/20"
        title="Check connection"
        @click="handleCheck"
      >
        <PhCheckCircle :size="18" class="text-success" />
      </button>
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
      <!-- Assigned Zones -->
      <div class="flex items-center gap-2">
        <PhLink :size="16" class="text-base-content/50" />
        <span class="text-sm font-medium text-base-content/70">Assigned Zones</span>
      </div>

      <div class="flex items-center gap-2">
        <span class="text-2xl font-bold text-base-content">{{ assignedZonesCount || 0 }}</span>
        <span class="text-xs text-base-content/50">zone{{ (assignedZonesCount || 0) !== 1 ? 's' : '' }}</span>
      </div>
    </div>

    <!-- Footer -->
    <template #footer>
      <div class="flex items-start justify-between gap-2">
        <!-- External Service -->
        <div v-if="externalService" class="flex items-center gap-2 min-w-0 flex-shrink">
          <PhPlugs :size="16" class="text-info flex-shrink-0" />
          <span class="text-xs text-base-content/60 truncate">{{ externalService.name }}</span>
        </div>
        <div v-else class="flex items-center gap-2">
          <PhWarningCircle :size="16" class="text-warning" />
          <span class="text-xs text-base-content/40">No service linked</span>
        </div>
      </div>
    </template>
  </EdgeMiningCard>

  <!-- Delete Confirmation -->
  <ConfirmDialog
    :open="showDeleteConfirm"
    title="Delete Climate Monitor"
    :message="`Are you sure you want to delete '${climateMonitor.name}'?`"
    confirm-text="Delete"
    confirm-class="btn-error"
    @confirm="confirmDelete"
    @cancel="cancelDelete"
  />
</template>

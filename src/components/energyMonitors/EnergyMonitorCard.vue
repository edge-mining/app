<script setup lang="ts">
import type { EnergyMonitor, EnergyMonitorAdapter } from "../../core/models/energyMonitor";
import type { EnergySource } from "../../core/models/energySource";
import { useExternalServiceStore } from "../../core/stores/externalServiceStore";
import { formatType } from "../../core/utils/index";
import { computed, ref } from "vue";
import {
  PhPencil,
  PhTrash,
  PhActivity,
  PhPlugs,
  PhLink,
  PhGear,
  PhHouse,
  PhBroadcast,
  PhLightning,
} from "@phosphor-icons/vue";
import ConfirmDialog from "../ConfirmDialog.vue";
import EdgeMiningCard, { type CardStyleConfig } from "../EdgeMiningCard.vue";
import ResourceId from "../ResourceId.vue";
import DummySolarIcon from "../icons/DummySolarIcon.vue";

const props = defineProps<{
  energyMonitor: EnergyMonitor;
  allEnergySources?: EnergySource[];
}>();

const emit = defineEmits<{
  edit: [energyMonitor: EnergyMonitor];
  delete: [energyMonitor: EnergyMonitor];
}>();

const externalServiceStore = useExternalServiceStore();
const showDeleteConfirm = ref(false);

// External service linked
const externalService = computed(() => {
  if (!props.energyMonitor.external_service_id) return null;
  return externalServiceStore.externalServices.find(
    (es) => es.id?.toString() === props.energyMonitor.external_service_id
  );
});

// Assigned energy sources
const assignedEnergySources = computed(() => {
  if (!props.allEnergySources || !props.energyMonitor.id) return [];
  return props.allEnergySources.filter(
    (es) => es.energy_monitor_id === props.energyMonitor.id
  );
});

// Adapter type configuration for styling
const adapterConfig = computed(() => {
  const type = props.energyMonitor.adapter_type;
  
  // Define configs for known adapter types
  const configs: Record<EnergyMonitorAdapter, { icon: typeof PhActivity; styleConfig: CardStyleConfig }> = {
    dummy_solar: {
      icon: DummySolarIcon as any,
      styleConfig: {
        gradient: "hover:from-amber-500/20 hover:to-orange-500/10",
        iconColor: "text-amber-400",
        badgeClass: "badge-warning",
        accentBorder: "border-l-base-300/50 hover:border-l-amber-500",
      },
    },
    home_assistant_api: {
      icon: PhHouse,
      styleConfig: {
        gradient: "hover:from-sky-500/20 hover:to-cyan-500/10",
        iconColor: "text-sky-400",
        badgeClass: "badge-info",
        accentBorder: "border-l-base-300/50 hover:border-l-sky-500",
      },
    },
    home_assistant_mqtt: {
      icon: PhBroadcast,
      styleConfig: {
        gradient: "hover:from-purple-500/20 hover:to-violet-500/10",
        iconColor: "text-purple-400",
        badgeClass: "bg-purple-500/20 text-purple-400",
        accentBorder: "border-l-base-300/50 hover:border-l-purple-500",
      },
    },
  };

  return (
    configs[type] || {
      icon: PhActivity,
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
  emit("edit", props.energyMonitor);
}

function handleDeleteClick() {
  showDeleteConfirm.value = true;
}

function confirmDelete() {
  showDeleteConfirm.value = false;
  emit("delete", props.energyMonitor);
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
      {{ energyMonitor.name }}
    </template>

    <!-- Badges -->
    <template #badges>
      <!-- Adapter Type Badge -->
      <span class="badge badge-sm max-w-[10rem] px-2 overflow-hidden" :class="adapterConfig.styleConfig.badgeClass" :title="formatType(energyMonitor.adapter_type)">
        <span class="marquee-on-overflow">{{ formatType(energyMonitor.adapter_type) }}</span>
      </span>
      
      <!-- ID -->
      <ResourceId v-if="energyMonitor.id" :id="energyMonitor.id" />
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
      <!-- Assigned Energy Sources -->
      <div class="flex items-center gap-2">
        <PhLightning :size="16" class="text-base-content/50" />
        <span class="text-sm font-medium text-base-content/70">Assigned Energy Sources</span>
      </div>
      
      <div v-if="assignedEnergySources.length > 0" class="space-y-2">
        <!-- Stats Row -->
        <div class="flex items-center gap-2">
          <span class="text-2xl font-bold text-base-content">{{ assignedEnergySources.length }}</span>
          <span class="text-xs text-base-content/50">energy source{{ assignedEnergySources.length !== 1 ? 's' : '' }}</span>
        </div>

        <!-- Energy Source Names -->
        <div class="flex flex-wrap gap-1.5">
          <span
            v-for="source in assignedEnergySources.slice(0, 4)"
            :key="source.id"
            class="badge badge-sm badge-ghost"
          >
            {{ source.name }}
          </span>
          <span
            v-if="assignedEnergySources.length > 4"
            class="badge badge-sm badge-ghost"
          >
            +{{ assignedEnergySources.length - 4 }} more
          </span>
        </div>
      </div>
      
      <div v-else class="text-sm text-base-content/40 italic py-2">
        No energy sources assigned
      </div>
    </div>

    <!-- Footer -->
    <template #footer>
      <div class="flex items-start justify-between gap-2">
        <!-- External Service -->
        <div v-if="externalService" class="flex items-center gap-2 min-w-0 flex-shrink">
          <div class="h-6 w-6 rounded-full bg-info/20 flex items-center justify-center flex-shrink-0">
            <PhPlugs :size="14" class="text-info" />
          </div>
          <div class="min-w-0">
            <div class="text-[10px] uppercase tracking-wider text-base-content/40">
              External Service
            </div>
            <div class="text-sm text-base-content/80 leading-tight truncate">
              {{ externalService.name }}
            </div>
          </div>
        </div>
        <div v-else class="flex items-center gap-2 text-base-content/30">
          <PhLink :size="14" />
          <span class="text-xs italic">No service linked</span>
        </div>

        <!-- Config indicator -->
        <div 
          v-if="energyMonitor.config && Object.keys(energyMonitor.config).length > 0"
          class="flex items-center gap-1 text-xs text-base-content/40 flex-shrink-0"
          :title="`${Object.keys(energyMonitor.config).length} config properties`"
        >
          <PhGear :size="14" />
          <span>{{ Object.keys(energyMonitor.config).length }} props</span>
        </div>
      </div>
    </template>
  </EdgeMiningCard>

  <!-- Delete Confirmation Dialog -->
  <ConfirmDialog
    :open="showDeleteConfirm"
    title="Delete Energy Monitor"
    :message="`Are you sure you want to delete '${energyMonitor.name}'? ${assignedEnergySources.length > 0 ? `This will unlink ${assignedEnergySources.length} energy source(s).` : ''}`"
    confirm-text="Delete"
    variant="danger"
    @confirm="confirmDelete"
    @cancel="cancelDelete"
  />
</template>

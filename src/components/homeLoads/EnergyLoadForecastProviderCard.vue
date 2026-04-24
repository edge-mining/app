<script setup lang="ts">
import type { EnergyLoadForecastProvider } from "../../core/models/energyLoadForecastProvider";
import type { LoadDevice } from "../../core/models/homeLoadsProfile";
import { useExternalServiceStore } from "../../core/stores/externalServiceStore";
import { formatType } from "../../core/utils/index";
import { computed, ref } from "vue";
import {
  PhPencil,
  PhTrash,
  PhBrain,
  PhPlugs,
  PhLink,
  PhGear,
} from "@phosphor-icons/vue";
import ConfirmDialog from "../ConfirmDialog.vue";
import EdgeMiningCard, { type CardStyleConfig } from "../EdgeMiningCard.vue";
import ResourceId from "../ResourceId.vue";

const props = defineProps<{
  provider: EnergyLoadForecastProvider;
  allDevices?: LoadDevice[];
}>();

const emit = defineEmits<{
  edit: [provider: EnergyLoadForecastProvider];
  delete: [provider: EnergyLoadForecastProvider];
}>();

const externalServiceStore = useExternalServiceStore();
const showDeleteConfirm = ref(false);

const externalService = computed(() => {
  if (!props.provider.external_service_id) return null;
  return externalServiceStore.externalServices.find(
    (es) => es.id?.toString() === props.provider.external_service_id
  );
});

const assignedDevices = computed(() => {
  if (!props.allDevices || !props.provider.id) return [];
  return props.allDevices.filter(
    (d) => d.energy_load_forecast_provider_id === props.provider.id
  );
});

const adapterConfig = computed(() => {
  const configs: Record<string, { icon: typeof PhBrain; styleConfig: CardStyleConfig }> = {
    dummy: {
      icon: PhGear,
      styleConfig: {
        gradient: "hover:from-slate-500/20 hover:to-gray-500/10",
        iconColor: "text-slate-400",
        badgeClass: "badge-neutral",
        accentBorder: "border-l-base-300/50 hover:border-l-slate-500",
      },
    },
    naive_last_hour: {
      icon: PhBrain,
      styleConfig: {
        gradient: "hover:from-teal-500/20 hover:to-emerald-500/10",
        iconColor: "text-teal-400",
        badgeClass: "bg-teal-500/20 text-teal-400",
        accentBorder: "border-l-base-300/50 hover:border-l-teal-500",
      },
    },
    seasonal_baseline: {
      icon: PhBrain,
      styleConfig: {
        gradient: "hover:from-amber-500/20 hover:to-orange-500/10",
        iconColor: "text-amber-400",
        badgeClass: "badge-warning",
        accentBorder: "border-l-base-300/50 hover:border-l-amber-500",
      },
    },
    statsmodels: {
      icon: PhBrain,
      styleConfig: {
        gradient: "hover:from-purple-500/20 hover:to-violet-500/10",
        iconColor: "text-purple-400",
        badgeClass: "bg-purple-500/20 text-purple-400",
        accentBorder: "border-l-base-300/50 hover:border-l-purple-500",
      },
    },
    xgboost: {
      icon: PhBrain,
      styleConfig: {
        gradient: "hover:from-sky-500/20 hover:to-cyan-500/10",
        iconColor: "text-sky-400",
        badgeClass: "badge-info",
        accentBorder: "border-l-base-300/50 hover:border-l-sky-500",
      },
    },
  };
  return (
    configs[props.provider.adapter_type] || {
      icon: PhBrain,
      styleConfig: {
        gradient: "hover:from-slate-500/20 hover:to-gray-500/10",
        iconColor: "text-slate-400",
        badgeClass: "badge-neutral",
        accentBorder: "border-l-base-300/50 hover:border-l-slate-500",
      },
    }
  );
});

function handleEdit() {
  emit("edit", props.provider);
}

function handleDeleteClick() {
  showDeleteConfirm.value = true;
}

function confirmDelete() {
  showDeleteConfirm.value = false;
  emit("delete", props.provider);
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
    <template #title>
      {{ provider.name }}
    </template>

    <template #badges>
      <span
        class="badge badge-sm max-w-[10rem] px-2 overflow-hidden"
        :class="adapterConfig.styleConfig.badgeClass"
        :title="formatType(provider.adapter_type)"
      >
        <span class="marquee-on-overflow">{{ formatType(provider.adapter_type) }}</span>
      </span>
      <ResourceId v-if="provider.id" :id="provider.id" />
    </template>

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

    <div class="space-y-3">
      <div class="flex items-center gap-2">
        <PhBrain :size="16" class="text-base-content/50" />
        <span class="text-sm font-medium text-base-content/70">Assigned Devices</span>
      </div>

      <div v-if="assignedDevices.length > 0" class="space-y-2">
        <div class="flex items-center gap-2">
          <span class="text-2xl font-bold text-base-content">{{ assignedDevices.length }}</span>
          <span class="text-xs text-base-content/50">device{{ assignedDevices.length !== 1 ? 's' : '' }}</span>
        </div>
        <div class="flex flex-wrap gap-1.5">
          <span
            v-for="device in assignedDevices.slice(0, 4)"
            :key="device.id"
            class="badge badge-sm badge-ghost"
          >
            {{ device.name }}
          </span>
          <span v-if="assignedDevices.length > 4" class="badge badge-sm badge-ghost">
            +{{ assignedDevices.length - 4 }} more
          </span>
        </div>
      </div>

      <div v-else class="text-sm text-base-content/40 italic py-2">
        No devices assigned
      </div>
    </div>

    <template #footer>
      <div class="flex items-start justify-between gap-2">
        <div v-if="externalService" class="flex items-center gap-2 min-w-0 flex-shrink">
          <div class="h-6 w-6 rounded-full bg-info/20 flex items-center justify-center flex-shrink-0">
            <PhPlugs :size="14" class="text-info" />
          </div>
          <div class="min-w-0">
            <div class="text-[10px] uppercase tracking-wider text-base-content/40">External Service</div>
            <div class="text-sm text-base-content/80 leading-tight truncate">{{ externalService.name }}</div>
          </div>
        </div>
        <div v-else class="flex items-center gap-2 text-base-content/30">
          <PhLink :size="14" />
          <span class="text-xs italic">No service linked</span>
        </div>
        <div
          v-if="provider.config && Object.keys(provider.config).length > 0"
          class="flex items-center gap-1 text-xs text-base-content/40 flex-shrink-0"
          :title="`${Object.keys(provider.config).length} config properties`"
        >
          <PhGear :size="14" />
          <span>{{ Object.keys(provider.config).length }} props</span>
        </div>
      </div>
    </template>
  </EdgeMiningCard>

  <ConfirmDialog
    :open="showDeleteConfirm"
    title="Delete Forecast Provider"
    :message="`Are you sure you want to delete '${provider.name}'?${assignedDevices.length > 0 ? ` This will unlink ${assignedDevices.length} device(s).` : ''}`"
    confirm-text="Delete"
    variant="danger"
    @confirm="confirmDelete"
    @cancel="cancelDelete"
  />
</template>

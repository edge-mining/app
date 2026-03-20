<script setup lang="ts">
import type { ForecastProvider, ForecastProviderAdapter } from "../../core/models/forecastProvider";
import type { EnergySource } from "../../core/models/energySource";
import { useExternalServiceStore } from "../../core/stores/externalServiceStore";
import { formatType } from "../../core/utils/index";
import { computed, ref } from "vue";
import {
  PhPencil,
  PhTrash,
  PhChartLine,
  PhPlugs,
  PhLink,
  PhGear,
  PhSun,
  PhLightning,
  PhHouse,
} from "@phosphor-icons/vue";
import ConfirmDialog from "../ConfirmDialog.vue";
import EdgeMiningCard, { type CardStyleConfig } from "../EdgeMiningCard.vue";
import ResourceId from "../ResourceId.vue";

const props = defineProps<{
  forecastProvider: ForecastProvider;
  allEnergySources?: EnergySource[];
}>();

const emit = defineEmits<{
  edit: [forecastProvider: ForecastProvider];
  delete: [forecastProvider: ForecastProvider];
}>();

const externalServiceStore = useExternalServiceStore();
const showDeleteConfirm = ref(false);

// External service linked
const externalService = computed(() => {
  if (!props.forecastProvider.external_service_id) return null;
  return externalServiceStore.externalServices.find(
    (es) => es.id?.toString() === props.forecastProvider.external_service_id
  );
});

// Assigned energy sources
const assignedEnergySources = computed(() => {
  if (!props.allEnergySources || !props.forecastProvider.id) return [];
  return props.allEnergySources.filter(
    (es) => es.forecast_provider_id === props.forecastProvider.id
  );
});

// Adapter type configuration for styling
const adapterConfig = computed(() => {
  const type = props.forecastProvider.adapter_type;

  const knownConfigs: Record<ForecastProviderAdapter, { icon: typeof PhChartLine; styleConfig: CardStyleConfig }> = {
    home_assistant_api: {
      icon: PhHouse,
      styleConfig: {
        gradient: "hover:from-sky-500/20 hover:to-cyan-500/10",
        iconColor: "text-sky-400",
        badgeClass: "badge-info",
        accentBorder: "border-l-base-300/50 hover:border-l-sky-500",
      },
    },
    dummy_solar: {
      icon: PhSun,
      styleConfig: {
        gradient: "hover:from-yellow-500/20 hover:to-amber-500/10",
        iconColor: "text-yellow-400",
        badgeClass: "bg-yellow-500/20 text-yellow-400",
        accentBorder: "border-l-base-300/50 hover:border-l-yellow-500",
      },
    },
  };

  return (
    knownConfigs[type] || {
      icon: PhChartLine,
      styleConfig: {
        gradient: "hover:from-indigo-500/20 hover:to-violet-500/10",
        iconColor: "text-indigo-400",
        badgeClass: "bg-indigo-500/20 text-indigo-400",
        accentBorder: "border-l-base-300/50 hover:border-l-indigo-500",
      },
    }
  );
});

function handleEdit() {
  emit("edit", props.forecastProvider);
}

function handleDeleteClick() {
  showDeleteConfirm.value = true;
}

function confirmDelete() {
  showDeleteConfirm.value = false;
  emit("delete", props.forecastProvider);
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
      {{ forecastProvider.name }}
    </template>

    <!-- Badges -->
    <template #badges>
      <!-- Adapter Type Badge -->
      <span class="badge badge-sm" :class="adapterConfig.styleConfig.badgeClass">
        {{ formatType(forecastProvider.adapter_type) }}
      </span>

      <!-- ID -->
      <ResourceId v-if="forecastProvider.id" :id="forecastProvider.id" />
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
          v-if="forecastProvider.config && Object.keys(forecastProvider.config).length > 0"
          class="flex items-center gap-1 text-xs text-base-content/40 flex-shrink-0"
          :title="`${Object.keys(forecastProvider.config).length} config properties`"
        >
          <PhGear :size="14" />
          <span>{{ Object.keys(forecastProvider.config).length }} props</span>
        </div>
      </div>
    </template>
  </EdgeMiningCard>

  <!-- Delete Confirmation Dialog -->
  <ConfirmDialog
    :open="showDeleteConfirm"
    title="Delete Forecast Provider"
    :message="`Are you sure you want to delete '${forecastProvider.name}'? ${assignedEnergySources.length > 0 ? `This will unlink ${assignedEnergySources.length} energy source(s).` : ''}`"
    confirm-text="Delete"
    variant="danger"
    @confirm="confirmDelete"
    @cancel="cancelDelete"
  />
</template>

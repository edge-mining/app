<script setup lang="ts">
import type {
  ExternalService,
  ExternalServiceStatus,
  ExternalServiceLinkedEntities,
} from "../../core/models/externalService";
import { useExternalServiceStore } from "../../core/stores/externalServiceStore";
import { formatType, formatTimeAgo } from "../../core/utils/index";
import { computed, onMounted, onUnmounted, ref } from "vue";
import {
  PhPencil,
  PhTrash,
  PhArrowClockwise,
  PhPlugs,
  PhGear,
  PhLink,
  PhCircle,
  PhActivity,
  PhChartLine,
  PhCpu,
  PhBell,
  PhHouse,
  PhWifiHigh,
  PhCloud,
} from "@phosphor-icons/vue";
import ConfirmDialog from "../ConfirmDialog.vue";
import EdgeMiningCard, { type CardStyleConfig } from "../EdgeMiningCard.vue";
import ResourceId from "../ResourceId.vue";

const props = defineProps<{
  externalService: ExternalService;
}>();

const emit = defineEmits<{
  edit: [externalService: ExternalService];
  delete: [externalService: ExternalService];
}>();

const externalServiceStore = useExternalServiceStore();
const showDeleteConfirm = ref(false);
const statusLoading = ref(false);

// Status
const status = computed<ExternalServiceStatus | undefined>(() => {
  if (!props.externalService.id) return undefined;
  return externalServiceStore.serviceStatuses.get(props.externalService.id);
});

// Linked entities
const linkedEntities = computed<ExternalServiceLinkedEntities | undefined>(() => {
  if (!props.externalService.id) return undefined;
  return externalServiceStore.serviceLinkedEntities.get(props.externalService.id);
});

const totalLinkedCount = computed(() => {
  if (!linkedEntities.value) return 0;
  return (
    linkedEntities.value.energy_monitors.length +
    linkedEntities.value.forecast_providers.length +
    linkedEntities.value.home_forecast_providers.length +
    linkedEntities.value.miner_controllers.length +
    linkedEntities.value.notifiers.length
  );
});

// Status config
const statusConfig = computed(() => {
  const configs: Record<string, { color: string; bgColor: string; badgeClass: string; statusClass: string; label: string }> = {
    connected: {
      color: "text-emerald-400",
      bgColor: "bg-emerald-500",
      badgeClass: "badge-success",
      statusClass: "status-success",
      label: "Connected",
    },
    disconnected: {
      color: "text-red-400",
      bgColor: "bg-red-500",
      badgeClass: "badge-error",
      statusClass: "status-error",
      label: "Disconnected",
    },
    unauthorized: {
      color: "text-amber-400",
      bgColor: "bg-amber-500",
      badgeClass: "badge-warning",
      statusClass: "status-warning",
      label: "Unauthorized",
    },
  };
  return configs[status.value?.status ?? ""] || {
    color: "text-base-content/40",
    bgColor: "bg-base-content/30",
    badgeClass: "badge-ghost",
    statusClass: "status-neutral",
    label: "Unknown",
  };
});

// Adapter type styling
const adapterConfig = computed(() => {
  const type = props.externalService.adapter_type;

  const knownConfigs: Record<string, { icon: typeof PhPlugs; styleConfig: CardStyleConfig }> = {
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
      icon: PhWifiHigh,
      styleConfig: {
        gradient: "hover:from-purple-500/20 hover:to-violet-500/10",
        iconColor: "text-purple-400",
        badgeClass: "bg-purple-500/20 text-purple-400",
        accentBorder: "border-l-base-300/50 hover:border-l-purple-500",
      },
    },
  };

  return (
    knownConfigs[type] || {
      icon: PhPlugs,
      styleConfig: {
        gradient: "hover:from-teal-500/20 hover:to-cyan-500/10",
        iconColor: "text-teal-400",
        badgeClass: "bg-teal-500/20 text-teal-400",
        accentBorder: "border-l-base-300/50 hover:border-l-teal-500",
      },
    }
  );
});

// Time ago tick
const now = ref(Date.now());
let tickInterval: ReturnType<typeof setInterval> | undefined;

const lastCheckAgo = computed(() => {
  if (!status.value?.last_check) return null;
  // eslint-disable-next-line @typescript-eslint/no-unused-expressions
  now.value; // reactive dependency for tick
  return formatTimeAgo(status.value.last_check);
});

onMounted(() => {
  tickInterval = setInterval(() => { now.value = Date.now(); }, 1000);
  if (props.externalService.id) {
    externalServiceStore.getServiceStatus(props.externalService.id);
    externalServiceStore.getLinkedEntities(props.externalService.id);
  }
});

onUnmounted(() => {
  if (tickInterval) clearInterval(tickInterval);
});

function refreshStatus() {
  if (!props.externalService.id) return;
  statusLoading.value = true;
  externalServiceStore.getServiceStatus(props.externalService.id).finally(() => {
    statusLoading.value = false;
  });
}

function handleEdit() {
  emit("edit", props.externalService);
}

function handleDeleteClick() {
  showDeleteConfirm.value = true;
}

function confirmDelete() {
  showDeleteConfirm.value = false;
  emit("delete", props.externalService);
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
      {{ externalService.name }}
    </template>

    <!-- Badges -->
    <template #badges>
      <!-- Adapter Type Badge -->
      <span class="badge badge-sm max-w-[10rem] px-2 overflow-hidden" :class="adapterConfig.styleConfig.badgeClass" :title="formatType(externalService.adapter_type)">
        <span class="marquee-on-overflow">{{ formatType(externalService.adapter_type) }}</span>
      </span>

      <!-- ID -->
      <ResourceId v-if="externalService.id" :id="externalService.id" />
    </template>

    <!-- Actions -->
    <template #actions>
      <button
        class="btn btn-ghost btn-sm btn-square hover:bg-base-content/10"
        title="Refresh status"
        :disabled="statusLoading"
        @click="refreshStatus"
      >
        <span v-if="statusLoading" class="loading loading-spinner loading-xs"></span>
        <PhArrowClockwise v-else :size="18" class="text-base-content/60" />
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
      <!-- Error Message -->
      <div
        v-if="status?.error_message"
        class="text-xs text-error bg-error/10 rounded-lg px-3 py-2 border border-error/20"
      >
        {{ status.error_message }}
      </div>

      <!-- Linked Entities -->
      <div class="flex items-center gap-2">
        <PhLink :size="16" class="text-base-content/50" />
        <span class="text-sm font-medium text-base-content/70">Linked Entities</span>
      </div>

      <div v-if="linkedEntities && totalLinkedCount > 0" class="space-y-2">
        <div class="flex items-center gap-2">
          <span class="text-2xl font-bold text-base-content">{{ totalLinkedCount }}</span>
          <span class="text-xs text-base-content/50">linked entity{{ totalLinkedCount !== 1 ? ' types' : '' }}</span>
        </div>

        <div class="flex flex-wrap gap-1.5">
          <span
            v-if="linkedEntities.energy_monitors.length > 0"
            class="badge badge-sm badge-ghost gap-1"
          >
            <PhActivity :size="12" />
            {{ linkedEntities.energy_monitors.length }} energy monitor{{ linkedEntities.energy_monitors.length !== 1 ? 's' : '' }}
          </span>
          <span
            v-if="linkedEntities.forecast_providers.length > 0"
            class="badge badge-sm badge-ghost gap-1"
          >
            <PhChartLine :size="12" />
            {{ linkedEntities.forecast_providers.length }} forecast provider{{ linkedEntities.forecast_providers.length !== 1 ? 's' : '' }}
          </span>
          <span
            v-if="linkedEntities.home_forecast_providers.length > 0"
            class="badge badge-sm badge-ghost gap-1"
          >
            <PhHouse :size="12" />
            {{ linkedEntities.home_forecast_providers.length }} home forecast provider{{ linkedEntities.home_forecast_providers.length !== 1 ? 's' : '' }}
          </span>
          <span
            v-if="linkedEntities.miner_controllers.length > 0"
            class="badge badge-sm badge-ghost gap-1"
          >
            <PhCpu :size="12" />
            {{ linkedEntities.miner_controllers.length }} miner controller{{ linkedEntities.miner_controllers.length !== 1 ? 's' : '' }}
          </span>
          <span
            v-if="linkedEntities.notifiers.length > 0"
            class="badge badge-sm badge-ghost gap-1"
          >
            <PhBell :size="12" />
            {{ linkedEntities.notifiers.length }} notifier{{ linkedEntities.notifiers.length !== 1 ? 's' : '' }}
          </span>
        </div>
      </div>

      <div v-else class="text-sm text-base-content/40 italic py-2">
        No entities linked
      </div>
    </div>

    <!-- Footer -->
    <template #footer>
      <div class="flex items-start justify-between gap-2">
        <!-- Connection Status -->
        <div class="flex items-center gap-2 min-w-0 flex-shrink">
          <div class="h-6 w-6 rounded-full flex items-center justify-center flex-shrink-0"
            :class="statusConfig.bgColor + '/20'"
          >
            <div class="inline-grid *:[grid-area:1/1]">
              <div v-if="status?.status === 'connected'" class="status" :class="statusConfig.statusClass + ' animate-ping'"></div>
              <div class="status" :class="statusConfig.statusClass"></div>
            </div>
          </div>
          <div class="min-w-0">
            <div class="text-[10px] uppercase tracking-wider text-base-content/40">
              Status
            </div>
            <div class="text-sm leading-tight truncate" :class="statusConfig.color">
              {{ statusConfig.label }}
            </div>
          </div>
        </div>

        <!-- Last Check -->
        <div class="flex items-center gap-2 min-w-0 flex-shrink">
          <div class="h-6 w-6 rounded-full bg-base-content/10 flex items-center justify-center flex-shrink-0">
            <PhArrowClockwise :size="14" class="text-base-content/40" />
          </div>
          <div class="min-w-0">
            <div class="text-[10px] uppercase tracking-wider text-base-content/40">
              Last Check
            </div>
            <div
              class="text-sm text-base-content/80 leading-tight truncate"
              :title="status?.last_check ? new Date(status.last_check).toLocaleString() : ''"
            >
              {{ lastCheckAgo ?? 'N/A' }}
            </div>
          </div>
        </div>

        <!-- Config indicator -->
        <div
          v-if="externalService.config && Object.keys(externalService.config).length > 0"
          class="flex items-center gap-1 text-xs text-base-content/40"
          :title="`${Object.keys(externalService.config).length} config properties`"
        >
          <PhGear :size="14" />
          <span>{{ Object.keys(externalService.config).length }} props</span>
        </div>
        <div v-else class="flex items-center gap-1 text-xs text-base-content/30">
          <PhGear :size="14" />
          <span class="italic">No config</span>
        </div>
      </div>
    </template>
  </EdgeMiningCard>

  <!-- Delete Confirmation Dialog -->
  <ConfirmDialog
    :open="showDeleteConfirm"
    title="Delete External Service"
    :message="`Are you sure you want to delete '${externalService.name}'? ${totalLinkedCount > 0 ? `This will unlink ${totalLinkedCount} entity(ies).` : ''}`"
    confirm-text="Delete"
    variant="danger"
    @confirm="confirmDelete"
    @cancel="cancelDelete"
  />
</template>

<script setup lang="ts">
import type { MinerController } from "../../core/models/minerController";
import type { Miner } from "../../core/models/miner";
import { useExternalServiceStore } from "../../core/stores/externalServiceStore";
import { computed, ref } from "vue";
import {
  PhHash,
  PhPencil,
  PhTrash,
  PhGear,
  PhCpu,
  PhLink,
  PhCircuitry,
  PhPlugs,
  PhLego,
  PhHardDrive,
  PhPlug,
} from "@phosphor-icons/vue";
import ConfirmDialog from "../ConfirmDialog.vue";
import EdgeMiningCard, { type CardStyleConfig } from "../EdgeMiningCard.vue";

const props = defineProps<{
  minerController: MinerController;
  allMiners?: Miner[];
}>();

const emit = defineEmits<{
  edit: [minerController: MinerController];
  delete: [minerController: MinerController];
}>();

const externalServiceStore = useExternalServiceStore();
const showDeleteConfirm = ref(false);

// External service linked
const externalService = computed(() => {
  if (!props.minerController.external_service_id) return null;
  return externalServiceStore.externalServices.find(
    (es) => es.id?.toString() === props.minerController.external_service_id
  );
});

// Assigned miners
const assignedMiners = computed(() => {
  if (!props.allMiners || !props.minerController.id) return [];
  return props.allMiners.filter(
    (miner) => miner.controller_id === props.minerController.id
  );
});

const activeAssignedMiners = computed(() => {
  return assignedMiners.value.filter((m) => m.active);
});

const runningAssignedMiners = computed(() => {
  return assignedMiners.value.filter((m) => m.status === "on");
});

// Adapter type configuration for styling
const adapterConfig = computed(() => {
  const type = props.minerController.adapter_type?.toLowerCase() || "";
  
  // Define configs for known adapter types
  const configs: Record<string, { icon: typeof PhGear; styleConfig: CardStyleConfig; badgeClass: string }> = {
    dummy: {
      icon: PhLego,
      badgeClass: "bg-slate-500/20 text-slate-400",
      styleConfig: {
        gradient: "hover:from-slate-500/20 hover:to-gray-500/10",
        iconColor: "text-slate-400",
        iconBgColor: "bg-slate-500/20",
        accentBorder: "border-l-base-300/50 hover:border-l-slate-500",
      },
    },
    pyasic: {
      icon: PhHardDrive,
      badgeClass: "bg-emerald-500/20 text-emerald-400",
      styleConfig: {
        gradient: "hover:from-emerald-500/20 hover:to-green-500/10",
        iconColor: "text-emerald-400",
        iconBgColor: "bg-emerald-500/20",
        accentBorder: "border-l-base-300/50 hover:border-l-emerald-500",
      },
    },
    generic_socket_home_assistant_api: {
      icon: PhPlug,
      badgeClass: "bg-sky-500/20 text-sky-400",
      styleConfig: {
        gradient: "hover:from-sky-500/20 hover:to-blue-500/10",
        iconColor: "text-sky-400",
        iconBgColor: "bg-sky-500/20",
        accentBorder: "border-l-base-300/50 hover:border-l-sky-500",
      },
    },
    vnish: {
      icon: PhCircuitry,
      badgeClass: "bg-cyan-500/20 text-cyan-400",
      styleConfig: {
        gradient: "hover:from-cyan-500/20 hover:to-teal-500/10",
        iconColor: "text-cyan-400",
        iconBgColor: "bg-cyan-500/20",
        accentBorder: "border-l-base-300/50 hover:border-l-cyan-500",
      },
    },
    awesome_miner: {
      icon: PhCpu,
      badgeClass: "bg-purple-500/20 text-purple-400",
      styleConfig: {
        gradient: "hover:from-purple-500/20 hover:to-violet-500/10",
        iconColor: "text-purple-400",
        iconBgColor: "bg-purple-500/20",
        accentBorder: "border-l-base-300/50 hover:border-l-purple-500",
      },
    },
    hiveos: {
      icon: PhGear,
      badgeClass: "bg-amber-500/20 text-amber-400",
      styleConfig: {
        gradient: "hover:from-amber-500/20 hover:to-yellow-500/10",
        iconColor: "text-amber-400",
        iconBgColor: "bg-amber-500/20",
        accentBorder: "border-l-base-300/50 hover:border-l-amber-500",
      },
    },
    foreman: {
      icon: PhGear,
      badgeClass: "bg-blue-500/20 text-blue-400",
      styleConfig: {
        gradient: "hover:from-blue-500/20 hover:to-sky-500/10",
        iconColor: "text-blue-400",
        iconBgColor: "bg-blue-500/20",
        accentBorder: "border-l-base-300/50 hover:border-l-blue-500",
      },
    },
  };

  return (
    configs[type] || {
      icon: PhGear,
      badgeClass: "bg-slate-500/20 text-slate-400",
      styleConfig: {
        gradient: "hover:from-slate-500/20 hover:to-gray-500/10",
        iconColor: "text-slate-400",
        iconBgColor: "bg-slate-500/20",
        accentBorder: "border-l-base-300/50 hover:border-l-slate-500",
      },
    }
  );
});

// Format adapter type for display
function formatAdapterType(type: string): string {
  return type
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

// Copy ID to clipboard
const idCopied = ref(false);
async function copyId() {
  if (!props.minerController.id) return;
  try {
    await navigator.clipboard.writeText(String(props.minerController.id));
    idCopied.value = true;
    setTimeout(() => (idCopied.value = false), 1500);
  } catch {
    const el = document.createElement("textarea");
    el.value = String(props.minerController.id);
    document.body.appendChild(el);
    el.select();
    document.execCommand("copy");
    document.body.removeChild(el);
    idCopied.value = true;
    setTimeout(() => (idCopied.value = false), 1500);
  }
}

function handleEdit() {
  emit("edit", props.minerController);
}

function handleDeleteClick() {
  showDeleteConfirm.value = true;
}

function confirmDelete() {
  showDeleteConfirm.value = false;
  emit("delete", props.minerController);
}

function cancelDelete() {
  showDeleteConfirm.value = false;
}
</script>

<template>
  <EdgeMiningCard
    :icon="adapterConfig.icon"
    :icon-size="26"
    :style-config="adapterConfig.styleConfig"
    card-class="min-h-[220px]"
  >
    <!-- Title Slot -->
    <template #title>
      <h3 class="text-lg font-semibold text-base-content leading-tight truncate">
        {{ minerController.name }}
      </h3>
    </template>

    <!-- Badges Slot -->
    <template #badges>
      <!-- Adapter Type Badge -->
      <span class="badge badge-sm" :class="adapterConfig.badgeClass">
        {{ formatAdapterType(minerController.adapter_type) }}
      </span>
      
      <!-- ID -->
      <button v-if="minerController.id"
        class="tooltip tooltip-top text-xs opacity-50 hover:opacity-100 transition-opacity flex items-center gap-0.5"
        :data-tip="idCopied ? 'Copied!' : `ID: ${minerController.id}`" @click="copyId">
        <PhHash :size="12" />
        <span class="font-mono text-left">{{ minerController.id.split('-')[0] }}</span>
      </button>
    </template>

    <!-- Actions Slot -->
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

    <!-- Main Content (default slot) -->
    <div class="py-1">
      <div class="flex items-center gap-2 mb-2">
        <PhCpu :size="16" class="text-base-content/50" />
        <span class="text-sm font-medium text-base-content/70">Assigned Miners</span>
      </div>
      
      <div v-if="assignedMiners.length > 0" class="space-y-2">
        <!-- Stats Row -->
        <div class="flex items-center gap-4">
          <div class="flex items-center gap-1.5">
            <span class="text-2xl font-bold text-base-content">{{ assignedMiners.length }}</span>
            <span class="text-xs text-base-content/50">total</span>
          </div>
          <div class="h-6 w-px bg-base-300/50"></div>
          <div class="flex items-center gap-1.5">
            <span class="text-lg font-semibold text-emerald-400">{{ runningAssignedMiners.length }}</span>
            <span class="text-xs text-base-content/50">running</span>
          </div>
          <div class="flex items-center gap-1.5">
            <span class="text-lg font-semibold text-sky-400">{{ activeAssignedMiners.length }}</span>
            <span class="text-xs text-base-content/50">active</span>
          </div>
        </div>

        <!-- Miner Names (collapsed, show first few) -->
        <div class="flex flex-wrap gap-1.5">
          <span
            v-for="miner in assignedMiners.slice(0, 4)"
            :key="miner.id"
            class="badge badge-sm badge-ghost"
            :class="{ 'badge-success badge-outline': miner.status === 'on' }"
          >
            {{ miner.name }}
          </span>
          <span
            v-if="assignedMiners.length > 4"
            class="badge badge-sm badge-ghost"
          >
            +{{ assignedMiners.length - 4 }} more
          </span>
        </div>
      </div>
      
      <div v-else class="text-sm text-base-content/40 italic py-2">
        No miners assigned
      </div>
    </div>

    <!-- Footer Slot -->
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
          v-if="minerController.config && Object.keys(minerController.config).length > 0"
          class="flex items-center gap-1 text-xs text-base-content/40 flex-shrink-0"
          :title="`${Object.keys(minerController.config).length} config properties`"
        >
          <PhGear :size="14" />
          <span>{{ Object.keys(minerController.config).length }} props</span>
        </div>
      </div>
    </template>
  </EdgeMiningCard>

  <!-- Delete Confirmation Dialog -->
  <ConfirmDialog
    :open="showDeleteConfirm"
    title="Delete Miner Controller"
    :message="`Are you sure you want to delete '${minerController.name}'? ${assignedMiners.length > 0 ? `This will unlink ${assignedMiners.length} miner(s).` : ''}`"
    confirm-text="Delete"
    variant="danger"
    @confirm="confirmDelete"
    @cancel="cancelDelete"
  />
</template>

<style scoped>
/* Component uses EdgeMiningCard base styles */
</style>

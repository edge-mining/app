<script setup lang="ts">
import type { Notifier } from "../../core/models/notifier";
import { useExternalServiceStore } from "../../core/stores/externalServiceStore";
import { formatType } from "../../core/utils/index";
import { computed, ref } from "vue";
import {
  PhPencil,
  PhTrash,
  PhBell,
  PhPlugs,
  PhLink,
  PhGear,
  PhPlay,
  PhTelegramLogo,
  PhEnvelope,
  PhWebhooksLogo,
  PhChatDots,
} from "@phosphor-icons/vue";
import ConfirmDialog from "../ConfirmDialog.vue";
import EdgeMiningCard, { type CardStyleConfig } from "../EdgeMiningCard.vue";
import ResourceId from "../ResourceId.vue";

const props = defineProps<{
  notifier: Notifier;
}>();

const emit = defineEmits<{
  edit: [notifier: Notifier];
  delete: [notifier: Notifier];
  test: [notifier: Notifier];
}>();

const externalServiceStore = useExternalServiceStore();
const showDeleteConfirm = ref(false);

// External service linked
const externalService = computed(() => {
  if (!props.notifier.external_service_id) return null;
  return externalServiceStore.externalServices.find(
    (es) => es.id?.toString() === props.notifier.external_service_id
  );
});

// Adapter type configuration for styling
const adapterConfig = computed(() => {
  const type = props.notifier.adapter_type;

  const knownConfigs: Record<string, { icon: typeof PhBell; styleConfig: CardStyleConfig }> = {
    telegram: {
      icon: PhTelegramLogo,
      styleConfig: {
        gradient: "hover:from-sky-500/20 hover:to-blue-500/10",
        iconColor: "text-sky-400",
        badgeClass: "badge-info",
        accentBorder: "border-l-base-300/50 hover:border-l-sky-500",
      },
    },
    email: {
      icon: PhEnvelope,
      styleConfig: {
        gradient: "hover:from-rose-500/20 hover:to-pink-500/10",
        iconColor: "text-rose-400",
        badgeClass: "bg-rose-500/20 text-rose-400",
        accentBorder: "border-l-base-300/50 hover:border-l-rose-500",
      },
    },
    webhook: {
      icon: PhWebhooksLogo,
      styleConfig: {
        gradient: "hover:from-emerald-500/20 hover:to-green-500/10",
        iconColor: "text-emerald-400",
        badgeClass: "bg-emerald-500/20 text-emerald-400",
        accentBorder: "border-l-base-300/50 hover:border-l-emerald-500",
      },
    },
    slack: {
      icon: PhChatDots,
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
      icon: PhBell,
      styleConfig: {
        gradient: "hover:from-amber-500/20 hover:to-orange-500/10",
        iconColor: "text-amber-400",
        badgeClass: "bg-amber-500/20 text-amber-400",
        accentBorder: "border-l-base-300/50 hover:border-l-amber-500",
      },
    }
  );
});

function handleEdit() {
  emit("edit", props.notifier);
}

function handleDeleteClick() {
  showDeleteConfirm.value = true;
}

function confirmDelete() {
  showDeleteConfirm.value = false;
  emit("delete", props.notifier);
}

function cancelDelete() {
  showDeleteConfirm.value = false;
}

function handleTest() {
  emit("test", props.notifier);
}
</script>

<template>
  <EdgeMiningCard
    :icon="adapterConfig.icon"
    :style-config="adapterConfig.styleConfig"
    card-class="min-h-[180px]"
  >
    <!-- Title -->
    <template #title>
      {{ notifier.name }}
    </template>

    <!-- Badges -->
    <template #badges>
      <!-- Adapter Type Badge -->
      <span class="badge badge-sm max-w-[10rem] px-2 overflow-hidden" :class="adapterConfig.styleConfig.badgeClass" :title="formatType(notifier.adapter_type)">
        <span class="marquee-on-overflow">{{ formatType(notifier.adapter_type) }}</span>
      </span>

      <!-- ID -->
      <ResourceId v-if="notifier.id" :id="notifier.id" />
    </template>

    <!-- Actions -->
    <template #actions>
      <button
        class="btn btn-ghost btn-sm btn-square hover:bg-info/20"
        title="Test notifier"
        @click="handleTest"
      >
        <PhPlay :size="18" class="text-info" />
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
      <!-- Test CTA -->
      <button
        class="btn btn-sm btn-outline btn-info gap-2 w-full"
        @click="handleTest"
      >
        <PhPlay :size="16" />
        Send Test Notification
      </button>
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
          v-if="notifier.config && Object.keys(notifier.config).length > 0"
          class="flex items-center gap-1 text-xs text-base-content/40 flex-shrink-0"
          :title="`${Object.keys(notifier.config).length} config properties`"
        >
          <PhGear :size="14" />
          <span>{{ Object.keys(notifier.config).length }} props</span>
        </div>
      </div>
    </template>
  </EdgeMiningCard>

  <!-- Delete Confirmation Dialog -->
  <ConfirmDialog
    :open="showDeleteConfirm"
    title="Delete Notifier"
    :message="`Are you sure you want to delete notifier '${notifier.name}'?`"
    confirm-text="Delete"
    variant="danger"
    @confirm="confirmDelete"
    @cancel="cancelDelete"
  />
</template>

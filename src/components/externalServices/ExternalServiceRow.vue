<script setup lang="ts">
import type { ExternalService, ExternalServiceStatus, ExternalServiceLinkedEntities } from "../../core/models/externalService";
import { computed, ref, onMounted } from "vue";
import { PhHash, PhPencil, PhTrash, PhArrowClockwise } from "@phosphor-icons/vue";
import { useExternalServiceStore } from "../../core/stores/externalServiceStore";
import ConfirmDialog from "../ConfirmDialog.vue";

const model = defineModel<ExternalService>({ required: true });
const emit = defineEmits<{
  edit: [externalService: ExternalService];
  delete: [externalService: ExternalService];
}>();

const externalServiceStore = useExternalServiceStore();
const showDeleteConfirm = ref(false);
const statusLoading = ref(false);

const status = computed<ExternalServiceStatus | undefined>(() => {
  if (!model.value.id) return undefined;
  return externalServiceStore.serviceStatuses.get(model.value.id);
});

const linkedEntities = computed<ExternalServiceLinkedEntities | undefined>(() => {
  if (!model.value.id) return undefined;
  return externalServiceStore.serviceLinkedEntities.get(model.value.id);
});

const linkedEntitiesText = computed(() => {
  if (!linkedEntities.value) return "-";
  const parts: string[] = [];
  if (linkedEntities.value.energy_monitors.length > 0) {
    parts.push(`${linkedEntities.value.energy_monitors.length} energy monitor(s)`);
  }
  if (linkedEntities.value.forecast_providers.length > 0) {
    parts.push(`${linkedEntities.value.forecast_providers.length} forecast provider(s)`);
  }
  if (linkedEntities.value.home_forecast_providers.length > 0) {
    parts.push(`${linkedEntities.value.home_forecast_providers.length} home forecast provider(s)`);
  }
  if (linkedEntities.value.miner_controllers.length > 0) {
    parts.push(`${linkedEntities.value.miner_controllers.length} miner controller(s)`);
  }
  if (linkedEntities.value.notifiers.length > 0) {
    parts.push(`${linkedEntities.value.notifiers.length} notifier(s)`);
  }
  return parts.length > 0 ? parts.join(", ") : "None";
});

const statusBadgeClass = computed(() => {
  if (!status.value) return "badge-ghost";
  switch (status.value.status) {
    case "connected": return "badge-success";
    case "disconnected": return "badge-error";
    case "unauthorized": return "badge-warning";
    default: return "badge-ghost";
  }
});

const statusText = computed(() => {
  if (!status.value) return "Unknown";
  return status.value.status.charAt(0).toUpperCase() + status.value.status.slice(1);
});

onMounted(() => {
  if (model.value.id) {
    externalServiceStore.getServiceStatus(model.value.id);
    externalServiceStore.getLinkedEntities(model.value.id);
  }
});

function refreshStatus() {
  if (!model.value.id) return;
  statusLoading.value = true;
  externalServiceStore.getServiceStatus(model.value.id).finally(() => {
    statusLoading.value = false;
  });
}

const externalServiceTip = ref<string | null>(null);

async function copyToClipboard(text: string) {
  try {
    await navigator.clipboard.writeText(text);
  } catch {
    const el = document.createElement("textarea");
    el.value = text;
    el.style.position = "fixed";
    el.style.left = "-9999px";
    document.body.appendChild(el);
    el.select();
    document.execCommand("copy");
    document.body.removeChild(el);
  }
}

function flashTip(original: string) {
  externalServiceTip.value = "Copied!";
  window.setTimeout(() => {
    externalServiceTip.value = original;
  }, 1200);
}

function handleEdit() {
  emit("edit", model.value);
}

function handleDeleteClick() {
  showDeleteConfirm.value = true;
}

function confirmDelete() {
  showDeleteConfirm.value = false;
  emit("delete", model.value);
}

function cancelDelete() {
  showDeleteConfirm.value = false;
}
</script>
<template>
  <tr>
    <th>
      <div class="flex items-center gap-3">
        <div class="text-xl flex items-center gap-1">
          <span
            v-if="model.id != null"
            class="tooltip tooltip-right id-tooltip"
            :data-tip="externalServiceTip ?? `ID: ${model.id}`"
          >
            <span
              role="button"
              tabindex="0"
              class="inline-flex cursor-pointer select-none opacity-70 hover:opacity-100"
              title="Copy external service ID"
              aria-label="Copy external service ID"
              @click.stop="copyToClipboard(String(model.id)); flashTip(`ID: ${model.id}`)"
              @keydown.enter.stop.prevent="copyToClipboard(String(model.id)); flashTip(`ID: ${model.id}`)"
              @keydown.space.stop.prevent="copyToClipboard(String(model.id)); flashTip(`ID: ${model.id}`)"
            >
              <PhHash class="size-3" />
            </span>
          </span>
          <span>{{ model.name }}</span>
        </div>
      </div>
    </th>
    <td>
      <div class="text-sm opacity-70">{{ model.adapter_type }}</div>
    </td>
    <td>
      <div class="flex items-center gap-2">
        <span class="badge badge-sm" :class="statusBadgeClass">{{ statusText }}</span>
        <button
          class="btn btn-xs btn-ghost"
          :class="{ 'loading loading-spinner loading-xs': statusLoading }"
          @click="refreshStatus"
          title="Refresh status"
          :disabled="statusLoading"
        >
          <PhArrowClockwise v-if="!statusLoading" :size="12" />
        </button>
      </div>
      <div v-if="status?.error_message" class="text-xs text-error opacity-70 mt-1">
        {{ status.error_message }}
      </div>
    </td>
    <td>
      <div class="text-sm opacity-70">{{ linkedEntitiesText }}</div>
    </td>
    <th>
      <div class="flex gap-2">
        <button class="btn btn-sm btn-primary" @click="handleEdit" title="Edit external service"><PhPencil :size="15" /></button>
        <button class="btn btn-sm btn-error" @click="handleDeleteClick" title="Delete external service"><PhTrash :size="15" /></button>
      </div>
    </th>
  </tr>

  <ConfirmDialog
    :open="showDeleteConfirm"
    title="Delete External Service"
    :message="`Are you sure you want to delete external service '${model.name}'?`"
    confirm-text="Delete"
    variant="danger"
    @confirm="confirmDelete"
    @cancel="cancelDelete"
  />
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import type { Notifier } from "../../core/models/notifier";
import { useExternalServiceStore } from "../../core/stores/externalServiceStore";
import { PhHash, PhPencil, PhTrash, PhPlay } from "@phosphor-icons/vue";
import ConfirmDialog from "../ConfirmDialog.vue";

const model = defineModel<Notifier>({ required: true });
const emit = defineEmits<{
  edit: [notifier: Notifier];
  delete: [notifier: Notifier];
  test: [notifier: Notifier];
}>();

const externalServiceStore = useExternalServiceStore();
const notifierTip = ref<string | null>(null);
const externalServiceIdTip = ref<string | null>(null);
const showDeleteConfirm = ref(false);

const externalService = computed(() => {
  if (!model.value.external_service_id) return null;
  return externalServiceStore.externalServices.find(
    (es) => es.id?.toString() === model.value.external_service_id
  );
});

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

function flashTip(target: "notifier" | "external", original: string) {
  const tipRef = target === "notifier" ? notifierTip : externalServiceIdTip;
  tipRef.value = "Copied!";
  window.setTimeout(() => {
    tipRef.value = original;
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

function handleTest() {
  emit("test", model.value);
}

// Format adapter type for display
const formatAdapterType = (type: string) => {
  return type
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
};
</script>
<template>
  <tr>
    <th>
      <div class="flex items-center gap-3">
        <div>
          <div class="text-xl flex items-center gap-1">
            <span
              v-if="model.id != null"
              class="tooltip tooltip-right id-tooltip"
              :data-tip="notifierTip ?? `ID: ${model.id}`"
            >
              <span
                role="button"
                tabindex="0"
                class="inline-flex cursor-pointer select-none opacity-70 hover:opacity-100"
                title="Copy notifier ID"
                aria-label="Copy notifier ID"
                @click.stop="copyToClipboard(String(model.id)); flashTip('notifier', `ID: ${model.id}`)"
                @keydown.enter.stop.prevent="copyToClipboard(String(model.id)); flashTip('notifier', `ID: ${model.id}`)"
                @keydown.space.stop.prevent="copyToClipboard(String(model.id)); flashTip('notifier', `ID: ${model.id}`)"
              >
                <PhHash class="size-3" />
              </span>
            </span>
            <span>{{ model.name }}</span>
          </div>
        </div>
      </div>
    </th>
    <td>{{ formatAdapterType(model.adapter_type) }}</td>
    <td>
      <div v-if="model.external_service_id">
        <div class="text-sm opacity-50 flex items-center gap-1">
          <span
            class="tooltip tooltip-top id-tooltip"
            :data-tip="externalServiceIdTip ?? `ID: ${model.external_service_id}`"
          >
            <span
              role="button"
              tabindex="0"
              class="inline-flex cursor-pointer select-none opacity-70 hover:opacity-100"
              title="Copy external service ID"
              aria-label="Copy external service ID"
              @click.stop="copyToClipboard(model.external_service_id); flashTip('external', `ID: ${model.external_service_id}`)"
              @keydown.enter.stop.prevent="copyToClipboard(model.external_service_id); flashTip('external', `ID: ${model.external_service_id}`)"
              @keydown.space.stop.prevent="copyToClipboard(model.external_service_id); flashTip('external', `ID: ${model.external_service_id}`)"
            >
              <PhHash class="size-3" />
            </span>
          </span>
          <span class="text-sm">{{ externalService?.name ?? "Unknown" }}</span>
        </div>
      </div>
      <div v-else class="text-sm opacity-50">-</div>
    </td>
    <th>
      <div class="flex gap-2">
        <button class="btn btn-sm btn-info" @click="handleTest" title="Test notifier"><PhPlay :size="15" /></button>
        <button class="btn btn-sm btn-primary" @click="handleEdit" title="Edit notifier"><PhPencil :size="15" /></button>
        <button class="btn btn-sm btn-error" @click="handleDeleteClick" title="Delete notifier"><PhTrash :size="15" /></button>
      </div>
    </th>
  </tr>

  <ConfirmDialog
    :open="showDeleteConfirm"
    title="Delete Notifier"
    :message="`Are you sure you want to delete notifier '${model.name}'?`"
    confirm-text="Delete"
    variant="danger"
    @confirm="confirmDelete"
    @cancel="cancelDelete"
  />
</template>

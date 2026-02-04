<script setup lang="ts">
import { ref } from "vue";
import type { OptimizationPolicy } from "../../core/models/policy";
import { PhHash, PhPencil, PhTrash } from "@phosphor-icons/vue";
import ConfirmDialog from "../ConfirmDialog.vue";

const model = defineModel<OptimizationPolicy>({ required: true });
const emit = defineEmits<{
  edit: [policy: OptimizationPolicy];
  delete: [policy: OptimizationPolicy];
  manageRules: [policy: OptimizationPolicy];
  check: [policy: OptimizationPolicy];
}>();

const optimizationPolicyTip = ref<string | null>(null);
const showDeleteConfirm = ref(false);

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
  const tipRef = optimizationPolicyTip;
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

function handleManageRules() {
  emit("manageRules", model.value);
}

function handleCheck() {
  emit("check", model.value);
}
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
              :data-tip="optimizationPolicyTip ?? `ID: ${model.id}`"
            >
              <span
                role="button"
                tabindex="0"
                class="inline-flex cursor-pointer select-none opacity-70 hover:opacity-100"
                title="Copy optimization policy ID"
                aria-label="Copy optimization policy ID"
                @click.stop="copyToClipboard(String(model.id)); flashTip(`ID: ${model.id}`)"
                @keydown.enter.stop.prevent="copyToClipboard(String(model.id)); flashTip(`ID: ${model.id}`)"
                @keydown.space.stop.prevent="copyToClipboard(String(model.id)); flashTip(`ID: ${model.id}`)"
              >
                <PhHash class="size-3" />
              </span>
            </span>
            <span>{{ model.name }}</span>
            <span v-if="model.metadata?.version" class="badge badge-sm badge-outline">v{{ model.metadata.version }}</span>
          </div>
          <div class="text-sm opacity-50">{{ model.description || 'No description' }}</div>
        </div>
      </div>
    </th>
    <td>
      <div class="flex flex-col gap-1 text-xs">
        <span v-if="model.metadata?.author" class="opacity-70">
          {{ model.metadata.author }}
        </span>
        <span v-else class="opacity-40">
          —
        </span>
      </div>
    </td>
    <td>
      <div class="flex flex-col gap-1 text-xs">
        <span v-if="model.metadata?.last_modified" class="opacity-70">
          {{ model.metadata.last_modified }}
        </span>
        <span v-else class="opacity-40">
          —
        </span>
      </div>
    </td>
    <td>
      <span class="badge badge-neutral">
        {{ model.start_rules?.length ?? 0 }} rules
      </span>
    </td>
    <td>
      <span class="badge badge-neutral">
        {{ model.stop_rules?.length ?? 0 }} rules
      </span>
    </td>
    <th>
      <div class="flex gap-2">
        <button class="btn btn-sm btn-secondary" @click="handleManageRules" title="Manage rules">
          Rules
        </button>
        <button class="btn btn-sm btn-info" @click="handleCheck" title="Check policy validity">
          Check
        </button>
        <button class="btn btn-sm btn-primary" @click="handleEdit" title="Edit optimization policy"><PhPencil :size="15" /></button>
        <button class="btn btn-sm btn-error" @click="handleDeleteClick" title="Delete optimization policy"><PhTrash :size="15" /></button>
      </div>
    </th>
  </tr>

  <ConfirmDialog
    :open="showDeleteConfirm"
    title="Delete Policy"
    :message="`Are you sure you want to delete policy '${model.name}'?`"
    confirm-text="Delete"
    variant="danger"
    @confirm="confirmDelete"
    @cancel="cancelDelete"
  />
</template>

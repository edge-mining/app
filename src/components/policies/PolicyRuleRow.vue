<script setup lang="ts">
import { ref } from "vue";
import type { AutomationRule } from "../../core/models/policy";
import { PhHash, PhPencil, PhTrash } from "@phosphor-icons/vue";
import ConfirmDialog from "../ConfirmDialog.vue";

const model = defineModel<AutomationRule>({ required: true });
const emit = defineEmits<{
  edit: [rule: AutomationRule];
  delete: [rule: AutomationRule];
  toggleEnabled: [rule: AutomationRule];
}>();

const automationRuleTip = ref<string | null>(null);
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
  automationRuleTip.value = "Copied!";
  window.setTimeout(() => {
    automationRuleTip.value = original;
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

function handleToggleEnabled() {
  emit("toggleEnabled", model.value);
}
</script>
<template>
  <tr>
    <th>
      <label>
        <input
          type="checkbox"
          class="toggle toggle-success toggle-sm"
          :checked="model.enabled"
          @change="handleToggleEnabled"
          title="Toggle rule enabled/disabled"
        />
      </label>
    </th>
    <td>
      <div class="flex items-center gap-3">
        <div>
          <div class="font-semibold flex items-center gap-1">
            <span
              v-if="model.id != null"
              class="tooltip tooltip-right id-tooltip"
              :data-tip="automationRuleTip ?? `ID: ${model.id}`"
            >
              <span
                role="button"
                tabindex="0"
                class="inline-flex cursor-pointer select-none opacity-70 hover:opacity-100"
                title="Copy automation rule ID"
                aria-label="Copy automation rule ID"
                @click.stop="copyToClipboard(String(model.id)); flashTip(`ID: ${model.id}`)"
                @keydown.enter.stop.prevent="copyToClipboard(String(model.id)); flashTip(`ID: ${model.id}`)"
                @keydown.space.stop.prevent="copyToClipboard(String(model.id)); flashTip(`ID: ${model.id}`)"
              >
                <PhHash class="size-3" />
              </span>
            </span>
            <span>{{ model.name }}</span>
          </div>
          <div class="text-sm opacity-50">{{ model.description || 'No description' }}</div>
        </div>
      </div>
    </td>
    <td>
      <span class="text-sm opacity-70">{{ model.priority ?? 0 }}</span>
    </td>
    <th>
      <div class="flex gap-2">
        <button class="btn btn-sm btn-primary" @click="handleEdit" title="Edit rule">
          <PhPencil :size="15" />
        </button>
        <button class="btn btn-sm btn-error" @click="handleDeleteClick" title="Delete rule">
          <PhTrash :size="15" />
        </button>
      </div>
    </th>
  </tr>

  <ConfirmDialog
    :open="showDeleteConfirm"
    title="Delete Rule"
    :message="`Are you sure you want to delete rule '${model.name}'?`"
    confirm-text="Delete"
    variant="danger"
    @confirm="confirmDelete"
    @cancel="cancelDelete"
  />
</template>

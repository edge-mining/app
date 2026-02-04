<script setup lang="ts">
import { ref } from "vue";
import type { OptimizationUnit } from "../../core/models/optimizationUnit";
import { PhPencil, PhTrash } from "@phosphor-icons/vue";
import ConfirmDialog from "../ConfirmDialog.vue";

const model = defineModel<OptimizationUnit>({ required: true });
const emit = defineEmits<{
  edit: [unit: OptimizationUnit];
  delete: [unit: OptimizationUnit];
  toggleEnabled: [unit: OptimizationUnit];
}>();

const showDeleteConfirm = ref(false);

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
          :checked="model.is_enabled"
          @change="handleToggleEnabled"
          title="Toggle enabled/disabled"
        />
      </label>
    </th>
    <td>
      <div class="flex items-center gap-3">
        <div>
          <div class="text-xl">{{ model.name || 'Unnamed Unit' }}</div>
          <div class="text-sm opacity-50">{{ model.description || 'No description' }}</div>
        </div>
      </div>
    </td>
    <td>
      <div class="text-sm opacity-70">
        {{ model.id ?? "-" }}
      </div>
    </td>
    <td>
      <div class="flex flex-wrap gap-1">
        <span class="badge badge-sm badge-outline" :title="'Miners: ' + model.target_miner_ids.length">
          {{ model.target_miner_ids.length }} miners
        </span>
        <span v-if="model.policy_id" class="badge badge-sm badge-primary" title="Has policy">
          Policy
        </span>
        <span v-if="model.energy_source_id" class="badge badge-sm badge-secondary" title="Has energy source">
          Energy
        </span>
        <span v-if="model.notifier_ids.length > 0" class="badge badge-sm badge-info" :title="'Notifiers: ' + model.notifier_ids.length">
          {{ model.notifier_ids.length }} notifiers
        </span>
      </div>
    </td>
    <th>
      <div class="flex gap-2">
        <button class="btn btn-sm btn-primary" @click="handleEdit" title="Edit optimization unit">
          <PhPencil :size="15" />
        </button>
        <button class="btn btn-sm btn-error" @click="handleDeleteClick" title="Delete optimization unit">
          <PhTrash :size="15" />
        </button>
      </div>
    </th>
  </tr>

  <ConfirmDialog
    :open="showDeleteConfirm"
    title="Delete Optimization Unit"
    :message="`Are you sure you want to delete optimization unit '${model.name}'?`"
    confirm-text="Delete"
    variant="danger"
    @confirm="confirmDelete"
    @cancel="cancelDelete"
  />
</template>

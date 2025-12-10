<script setup lang="ts">
import type { Policy } from "../../core/models/policy";

const model = defineModel<Policy>({ required: true });
const emit = defineEmits<{
  edit: [policy: Policy];
  delete: [policy: Policy];
  manageRules: [policy: Policy];
  check: [policy: Policy];
}>();

function handleEdit() {
  emit("edit", model.value);
}

function handleDelete() {
  if (confirm(`Are you sure you want to delete policy "${model.value.name}"?`)) {
    emit("delete", model.value);
  }
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
      <label>
        <input type="checkbox" class="checkbox" />
      </label>
    </th>
    <td>
      <div class="flex items-center gap-3">
        <div>
          <div class="text-xl">{{ model.name }}</div>
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
      <span
        :class="[
          'badge',
          model.enabled ? 'badge-success' : 'badge-ghost'
        ]"
      >
        {{ model.enabled ? 'Enabled' : 'Disabled' }}
      </span>
    </td>
    <td>
      <span class="badge badge-neutral">
        {{ model.rules?.length ?? 0 }} rules
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
        <button class="btn btn-sm btn-primary" @click="handleEdit" title="Edit policy">
          Edit
        </button>
        <button class="btn btn-sm btn-error" @click="handleDelete" title="Delete policy">
          Delete
        </button>
      </div>
    </th>
  </tr>
</template>

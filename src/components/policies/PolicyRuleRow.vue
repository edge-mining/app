<script setup lang="ts">
import type { PolicyRule } from "../../core/models/policy";

const model = defineModel<PolicyRule>({ required: true });
const emit = defineEmits<{
  edit: [rule: PolicyRule];
  delete: [rule: PolicyRule];
  toggleEnabled: [rule: PolicyRule];
}>();

function handleEdit() {
  emit("edit", model.value);
}

function handleDelete() {
  if (confirm(`Are you sure you want to delete rule "${model.value.name}"?`)) {
    emit("delete", model.value);
  }
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
          <div class="font-semibold">{{ model.name }}</div>
          <div class="text-sm opacity-50">{{ model.description || 'No description' }}</div>
        </div>
      </div>
    </td>
    <td>
      <span class="badge badge-outline">{{ model.rule_type }}</span>
    </td>
    <td>
      <span class="text-sm opacity-70">{{ model.priority ?? 0 }}</span>
    </td>
    <th>
      <div class="flex gap-2">
        <button class="btn btn-sm btn-primary" @click="handleEdit" title="Edit rule">
          Edit
        </button>
        <button class="btn btn-sm btn-error" @click="handleDelete" title="Delete rule">
          Delete
        </button>
      </div>
    </th>
  </tr>
</template>

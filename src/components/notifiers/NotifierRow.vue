<script setup lang="ts">
import type { Notifier } from "../../core/models/notifier";

const model = defineModel<Notifier>({ required: true });
const emit = defineEmits<{
  edit: [notifier: Notifier];
  delete: [notifier: Notifier];
  test: [notifier: Notifier];
}>();

function handleEdit() {
  emit("edit", model.value);
}

function handleDelete() {
  if (confirm(`Are you sure you want to delete notifier "${model.value.name}"?`)) {
    emit("delete", model.value);
  }
}

function handleTest() {
  emit("test", model.value);
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
          <div class="text-sm opacity-50">{{ model.adapter_type }}</div>
        </div>
      </div>
    </td>
    <td>
      <div class="text-sm opacity-70">
        {{ model.id ?? "-" }}
      </div>
    </td>
    <th>
      <div class="flex gap-2">
        <button class="btn btn-sm btn-info" @click="handleTest" title="Test notifier">
          Test
        </button>
        <button class="btn btn-sm btn-primary" @click="handleEdit" title="Edit notifier">
          Edit
        </button>
        <button class="btn btn-sm btn-error" @click="handleDelete" title="Delete notifier">
          Delete
        </button>
      </div>
    </th>
  </tr>
</template>

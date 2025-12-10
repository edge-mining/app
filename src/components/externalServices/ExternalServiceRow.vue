<script setup lang="ts">
import type { ExternalService } from "../../core/models/externalService";

const model = defineModel<ExternalService>({ required: true });
const emit = defineEmits<{
  edit: [externalService: ExternalService];
  delete: [externalService: ExternalService];
}>();

function handleEdit() {
  emit("edit", model.value);
}

function handleDelete() {
  if (confirm(`Are you sure you want to delete external service "${model.value.name}"?`)) {
    emit("delete", model.value);
  }
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
        <button class="btn btn-sm btn-primary" @click="handleEdit" title="Edit external service">
          Edit
        </button>
        <button class="btn btn-sm btn-error" @click="handleDelete" title="Delete external service">
          Delete
        </button>
      </div>
    </th>
  </tr>
</template>

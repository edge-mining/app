<script setup lang="ts">
import type { EnergySource } from "../../core/models/energySource";

const model = defineModel<EnergySource>({ required: true });
const emit = defineEmits<{
  edit: [energySource: EnergySource];
  delete: [energySource: EnergySource];
}>();

function handleEdit() {
  emit("edit", model.value);
}

function handleDelete() {
  if (confirm(`Are you sure you want to delete energy source "${model.value.name}"?`)) {
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
          <div class="text-sm opacity-50">{{ model.type }}</div>
        </div>
      </div>
    </td>
    <td>
      <div class="text-xl">
        {{ model.nominal_power_max ?? "-" }} kW
      </div>
    </td>
    <td>
      <div class="text-xl">
        {{ model.storage?.nominal_capacity ?? "-" }} kWh
      </div>
    </td>
    <td>
      <div class="text-xl">
        {{ model.grid?.contracted_power ?? "-" }} kW
      </div>
    </td>
    <td>
      <div class="text-sm opacity-70">
        {{ model.energy_monitor_id ?? "-" }}
      </div>
    </td>
    <th>
      <div class="flex gap-2">
        <button class="btn btn-sm btn-primary" @click="handleEdit" title="Edit energy source">
          ✏️
        </button>
        <button class="btn btn-sm btn-error" @click="handleDelete" title="Delete energy source">
          🗑️
        </button>
      </div>
    </th>
  </tr>
</template>

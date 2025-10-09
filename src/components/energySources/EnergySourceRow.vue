<script setup lang="ts">
import type { EnergySource } from "../../core/models/energySource";

const model = defineModel<EnergySource>({ required: true });
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
    <th></th>
  </tr>
</template>

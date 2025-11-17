<script setup lang="ts">
import type { EnergyMonitor } from "../../core/models/energyMonitor";

const model = defineModel<EnergyMonitor>({ required: true });
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
        {{ model.external_service_id ?? "-" }}
      </div>
    </td>
    <th></th>
  </tr>
</template>

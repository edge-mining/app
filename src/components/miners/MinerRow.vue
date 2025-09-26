<script setup lang="ts">
import type { Miner } from "../../core/models/miner";

const model = defineModel<Miner>({ required: true });
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
        <!-- <div class="avatar">
          <div class="mask mask-squircle h-12 w-12">
            <img
                    src="https://img.daisyui.com/images/profile/demo/2@94.webp"
                    alt="Avatar Tailwind CSS Component"
                  />
          </div>
        </div> -->
        <div>
          <div class="text-xl">{{ model.name }}</div>
          <div class="text-sm opacity-50">{{ model.active }}</div>
        </div>
      </div>
    </td>
    <td>
      <div
        class="text-xl"
        :class="model.status === 'active' ? 'text-green-500' : 'text-red-500'"
      >
        {{ model.status }}
      </div>
    </td>
    <td>
      <div class="text-xl">
        {{ model.hash_rate?.value }} {{ model.hash_rate?.unit }}
      </div>
      <div class="text-sm opacity-50">
        ({{ model.hash_rate_max?.value }} {{ model.hash_rate_max?.unit }})
      </div>
    </td>
    <td>
      <div class="text-xl">{{ model.power_consumption }} Watts</div>
      <div class="text-sm opacity-50">
        ({{ model.power_consumption_max }} Watts)
      </div>
    </td>
    <th></th>
  </tr>
</template>

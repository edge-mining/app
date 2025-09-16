<script setup lang="ts">
import { onMounted } from "vue";
import { useMinerStore } from "../../core/stores/minerStore";

const minerStore = useMinerStore();

onMounted(() => {
  minerStore.loadMiners();
});
</script>

<template>
  <h1 class="text-3xl font-bold">Miners settings</h1>

  <div class="overflow-x-auto">
    <table class="table">
      <!-- head -->
      <thead>
        <tr>
          <th>
            <!-- <label>
              <input type="checkbox" class="checkbox" />
            </label> -->
          </th>
          <th>Name</th>
          <th>Status</th>
          <th>Hash Rate (Max)</th>
          <th>Power Consumption (Max)</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="miner in minerStore.miners" :key="miner.id">
          <th>
            <label>
              <input type="checkbox" class="checkbox" />
            </label>
          </th>
          <td>
            <div class="flex items-center gap-3">
              <div class="avatar">
                <div class="mask mask-squircle h-12 w-12">
                  <!-- <img
                    src="https://img.daisyui.com/images/profile/demo/2@94.webp"
                    alt="Avatar Tailwind CSS Component"
                  /> -->
                </div>
              </div>
              <div>
                <div class="text-xl">{{ miner.name }}</div>
                <div class="text-sm opacity-50">{{ miner.active }}</div>
              </div>
            </div>
          </td>
          <td>
            <div
              class="text-xl"
              :class="
                miner.status === 'active' ? 'text-green-500' : 'text-red-500'
              "
            >
              {{ miner.status }}
            </div>
          </td>
          <td>
            <div class="text-xl">
              {{ miner.hash_rate?.value }} {{ miner.hash_rate?.unit }}
            </div>
            <div class="text-sm opacity-50">
              ({{ miner.hash_rate_max?.value }} {{ miner.hash_rate_max?.unit }})
            </div>
          </td>
          <td>
            <div class="text-xl">{{ miner.power_consumption }} Watts</div>
            <div class="text-sm opacity-50">
              ({{ miner.power_consumption_max }} Watts)
            </div>
          </td>
          <th></th>
        </tr>

        <tr>
          <th colspan="5" class="text-center">
            <button class="btn btn-primary">Add Miner</button>
          </th>
          <!-- {
          Example of required data to create a miner
            "name": "",
            "hash_rate_max": {
              "value": 0,
              "unit": "TH/s"
            },
            "power_consumption_max": 0,
            "controller_id": "string"
          } -->
        </tr>
      </tbody>
      <!-- foot -->
      <tfoot>
        <tr>
          <th></th>
          <th>Name</th>
          <th>Status</th>
          <th>Hash Rate (Max)</th>
          <th>Power Consumption (Max)</th>
          <th></th>
        </tr>
      </tfoot>
    </table>
  </div>
</template>

<style scoped></style>

<script setup lang="ts">
import { onMounted } from "vue";
import { useMinerStore } from "../../core/stores/minerStore";

const minerStore = useMinerStore();

onMounted(() => {
  minerStore.loadMiners();
});
</script>

<template>
  <h1 class="text-3xl font-bold underline">Miners settings!</h1>

  <!-- <div>
    <span v-for="value in minerStore.miners" :key="value.id">{{
      value.name
    }}</span>
  </div> -->

  <!-- <div class="stats shadow" v-for="miner in minerStore.miners" :key="miner.id">
    <div class="stat">
      <div class="stat-title">{{ miner.name }}</div>
      <div class="stat-value">
        {{ miner.hash_rate?.value }} {{ miner.hash_rate?.unit }}
      </div>
      <div class="stat-desc">{{ miner.status }}</div>
      <div class="stat-desc">{{ miner.power_consumption }} Watts</div>
    </div>
  </div> -->

  <!-- <div
    class="card bg-base-100 card-border border-base-300 card-sm w-96 shadow-sm"
    v-for="miner in minerStore.miners"
    :key="miner.id"
  >
    <div class="card-body">
      <h2 class="card-title">{{ miner.name }}</h2>
      <p><span>{{ miner.hash_rate?.value }} {{ miner.hash_rate?.unit }}</span></p>
      <p>{{ miner.status }}</p>
      <p>{{ miner.power_consumption }} Watts</p>
    </div>
  </div> -->

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
          <th></th>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <th>
            <button class="btn btn-primary">Add Miner</button>
          </th>
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

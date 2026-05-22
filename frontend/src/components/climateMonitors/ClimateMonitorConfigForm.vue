<script setup lang="ts">
import { computed } from "vue";
import type { ClimateMonitorConfig } from "../../core/models/climateMonitor";
import { ClimateMonitorAdapter } from "../../core/models/climateMonitor";
import ConfigSchemaForm from "../ConfigSchemaForm.vue";

const props = defineProps<{
  adapterType: string;
}>();

const config = defineModel<ClimateMonitorConfig>({ required: true });

const needsSensorPrefix = computed(() =>
  props.adapterType === ClimateMonitorAdapter.HOME_ASSISTANT_API
);
</script>

<template>
  <ConfigSchemaForm
    v-model="config"
    :adapter-type="adapterType"
    config-endpoint="climate-monitors"
    :sensor-prefix="needsSensorPrefix"
  />
</template>

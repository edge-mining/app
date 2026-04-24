<script setup lang="ts">
import { computed } from "vue";
import type { EnergyMonitorConfig } from "../../core/models/energyMonitor";
import { EnergyMonitorAdapter } from "../../core/models/energyMonitor";
import ConfigSchemaForm from "../ConfigSchemaForm.vue";

const props = defineProps<{
	adapterType: string;
}>();

const config = defineModel<EnergyMonitorConfig>({ required: true });

const needsSensorPrefix = computed(() =>
	props.adapterType === EnergyMonitorAdapter.HOME_ASSISTANT_API
	|| props.adapterType === EnergyMonitorAdapter.HOME_ASSISTANT_MQTT
);
</script>

<template>
	<ConfigSchemaForm
		v-model="config"
		:adapter-type="adapterType"
		config-endpoint="energy-monitors"
		:sensor-prefix="needsSensorPrefix"
	/>
</template>


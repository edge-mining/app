<script setup lang="ts">
import type { ForecastProviderConfig } from "../../core/models/forecastProvider";
import ConfigSchemaForm from "../ConfigSchemaForm.vue";

defineProps<{
	adapterType: string;
}>();

const config = defineModel<ForecastProviderConfig>({ required: true });
</script>

<template>
	<ConfigSchemaForm
		v-model="config"
		:adapter-type="adapterType"
		config-endpoint="forecast-providers"
	/>
</template>

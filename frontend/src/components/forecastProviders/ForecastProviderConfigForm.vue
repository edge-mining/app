<script setup lang="ts">
import { computed } from "vue";
import type { ForecastProviderConfig } from "../../core/models/forecastProvider";
import { ForecastProviderAdapter } from "../../core/models/forecastProvider";
import ConfigSchemaForm from "../ConfigSchemaForm.vue";

const props = defineProps<{
	adapterType: string;
}>();

const config = defineModel<ForecastProviderConfig>({ required: true });

const needsEntityPrefix = computed(
	() => props.adapterType === ForecastProviderAdapter.HOME_ASSISTANT_API
);
</script>

<template>
	<ConfigSchemaForm
		v-model="config"
		:adapter-type="adapterType"
		config-endpoint="forecast-providers"
		:sensor-prefix="needsEntityPrefix"
	/>
</template>

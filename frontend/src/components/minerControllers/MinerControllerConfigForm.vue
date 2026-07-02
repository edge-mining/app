<script setup lang="ts">
import { computed } from "vue";
import type { MinerControllerConfig } from "../../core/models/minerController";
import { MinerControllerAdapter } from "../../core/models/minerController";
import ConfigSchemaForm from "../ConfigSchemaForm.vue";

const props = defineProps<{
	adapterType: string;
}>();

const config = defineModel<MinerControllerConfig>({ required: true });

const needsEntityPrefix = computed(
	() => props.adapterType === MinerControllerAdapter.GENERIC_SOCKET_HOME_ASSISTANT_API
);
</script>

<template>
	<ConfigSchemaForm
		v-model="config"
		:adapter-type="adapterType"
		config-endpoint="miner-controllers"
		:sensor-prefix="needsEntityPrefix"
	/>
</template>

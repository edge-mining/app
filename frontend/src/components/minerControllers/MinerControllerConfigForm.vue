<script setup lang="ts">
import type { MinerControllerConfig } from "../../core/models/minerController";
import ConfigSchemaForm from "../ConfigSchemaForm.vue";

defineProps<{
	adapterType: string;
}>();

const config = defineModel<MinerControllerConfig>({ required: true });
</script>

<template>
	<ConfigSchemaForm
		v-model="config"
		:adapter-type="adapterType"
		config-endpoint="miner-controllers"
	/>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from "vue";
import { useNotifierStore } from "../../core/stores/notifierStore";
import type { NotifierConfig, ConfigSchema } from "../../core/models/notifier";

const model = defineModel<NotifierConfig>({ required: true });
const props = defineProps<{
  adapterType: string;
}>();

const notifierStore = useNotifierStore();
const schema = ref<ConfigSchema | null>(null);
const loading = ref(false);

async function loadSchema() {
  if (!props.adapterType) return;

  loading.value = true;
  try {
    const cached = notifierStore.configSchemas.get(props.adapterType);
    if (cached) {
      schema.value = cached;
    } else {
      schema.value = await notifierStore.loadConfigSchema(props.adapterType);
    }

    // Initialize model with default values if empty
    if (schema.value && Object.keys(model.value).length === 0) {
      const defaults: NotifierConfig = {};
      for (const [key, prop] of Object.entries(schema.value.properties)) {
        if (prop.default !== undefined) {
          defaults[key] = prop.default;
        }
      }
      model.value = defaults;
    }
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  loadSchema();
});

watch(() => props.adapterType, () => {
  schema.value = null;
  model.value = {};
  loadSchema();
});

function getInputType(schemaType: string): string {
  switch (schemaType) {
    case "integer":
    case "number":
      return "number";
    case "boolean":
      return "checkbox";
    default:
      return "text";
  }
}
</script>

<template>
  <div v-if="loading" class="flex justify-center p-4">
    <span class="loading loading-spinner loading-md"></span>
  </div>

  <div v-else-if="schema" class="flex flex-col gap-3">
    <div v-for="(prop, key) in schema.properties" :key="key" class="space-y-1">
      <div class="font-medium">
        {{ prop.title }}
        <span v-if="schema.required?.includes(String(key))" class="text-sm text-error opacity-60 ml-1 font-normal">(required)</span>
        <span v-if="!schema.required?.includes(String(key))" class="text-sm opacity-60 ml-1 font-normal">(optional)</span>
      </div>

      <template v-if="prop.type === 'boolean'">
        <label class="flex items-center gap-2 cursor-pointer">
          <input
            v-model="model[key]"
            type="checkbox"
            class="checkbox checkbox-sm"
          />
          <span class="text-sm">
            {{ prop.description || 'Enable' }}
          </span>
        </label>
      </template>

      <template v-else>
        <input
          v-model="model[key]"
          :type="getInputType(prop.type)"
          :placeholder="prop.description || prop.title"
          :required="schema.required?.includes(String(key))"
          class="input input-bordered input-sm w-full"
        />
      </template>

      <div v-if="prop.description && prop.type !== 'boolean'" class="text-sm italic opacity-70">
        {{ prop.description }}
      </div>
    </div>

    <div v-if="Object.keys(schema.properties).length === 0" class="text-center text-base-content/50 py-2">
      No configuration required for this adapter type.
    </div>
  </div>

  <div v-else class="text-center text-base-content/50 py-2">
    Select an adapter type to see configuration options.
  </div>
</template>

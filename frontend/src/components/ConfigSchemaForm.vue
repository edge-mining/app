<script setup lang="ts">
import { ref, watch } from "vue";
import { BaseService } from "../core/services/baseService";
import { PhEye, PhEyeSlash } from "@phosphor-icons/vue";

interface ConfigSchemaProperty {
	type?: string;
	title?: string;
	description?: string;
	default?: any;
	$ref?: string;
	anyOf?: any[];
	enum?: any[];
	properties?: Record<string, ConfigSchemaProperty>;
	minimum?: number;
	maximum?: number;
	required?: string[];
}

interface ConfigSchema {
	title?: string;
	description?: string;
	type?: string;
	properties: Record<string, ConfigSchemaProperty>;
	required?: string[];
	$defs?: Record<string, ConfigSchemaProperty>;
}

const props = withDefaults(defineProps<{
	/** Adapter type string — triggers schema reload when changed. */
	adapterType: string;
	/** API endpoint base, e.g. "energy-monitors" or "energy-load-history-providers".
	 *  The component calls /{configEndpoint}/types/{adapterType}/config-schema */
	configEndpoint: string;
	/** If true, string fields whose name contains "entity" get a "sensor." prefix
	 *  (Home Assistant convention). */
	sensorPrefix?: boolean;
}>(), {
	sensorPrefix: false,
});

const config = defineModel<Record<string, any>>({ required: true });

const service = new BaseService();
const schema = ref<ConfigSchema | null>(null);
const loading = ref(false);
const passwordVisibility = ref<Record<string, boolean>>({});

// ── Schema helpers ──────────────────────────────────────────────

const resolveRef = (refStr: string, s: ConfigSchema): any => {
	if (!refStr.startsWith("#/$defs/")) return null;
	return s.$defs?.[refStr.replace("#/$defs/", "")] || null;
};

const getPropertySchema = (property: any, s: ConfigSchema): any => {
	if (property.$ref) return resolveRef(property.$ref, s);
	if (property.anyOf) {
		const nonNull = property.anyOf.find((i: any) => i.type !== "null");
		if (nonNull) {
			if (nonNull.$ref) return resolveRef(nonNull.$ref, s);
			return { ...property, ...nonNull, anyOf: undefined };
		}
	}
	return property;
};

const isNullable = (property: any): boolean =>
	!!property.anyOf?.some((i: any) => i.type === "null");

const initializeDefaultValue = (property: any, s: ConfigSchema): any => {
	if (property.default !== undefined) return property.default;
	const resolved = getPropertySchema(property, s);
	if (resolved?.default !== undefined) return resolved.default;
	if (isNullable(property)) return null;
	if (resolved?.enum) return resolved.enum[0];
	if (resolved?.type === "object" && resolved?.properties) {
		const obj: any = {};
		Object.entries(resolved.properties).forEach(([k, p]: [string, any]) => {
			obj[k] = initializeDefaultValue(p, s);
		});
		return obj;
	}
	if (resolved?.type === "string") return "";
	if (resolved?.type === "number" || resolved?.type === "integer") return 0;
	if (resolved?.type === "boolean") return false;
	return null;
};

// ── Schema fetch ────────────────────────────────────────────────

watch(
	() => props.adapterType,
	async (newAdapterType) => {
		if (!newAdapterType) {
			schema.value = null;
			return;
		}
		loading.value = true;
		try {
			const resp = await service.get<ConfigSchema>(
				`/${props.configEndpoint}/types/${newAdapterType}/config-schema`
			);
			schema.value = resp.data;

			if (schema.value?.properties) {
				const existing = { ...config.value };
				const fresh: Record<string, any> = {};
				Object.entries(schema.value.properties).forEach(([key, property]) => {
					fresh[key] =
						existing[key] !== undefined
							? existing[key]
							: initializeDefaultValue(property, schema.value!);
				});
				config.value = fresh;
			}
		} catch (error) {
			console.error("Failed to load config schema:", error);
			schema.value = null;
		} finally {
			loading.value = false;
		}
	},
	{ immediate: true }
);

// ── Display helpers ─────────────────────────────────────────────

const formatFieldName = (name: string) =>
	name
		.split("_")
		.map((w) => w.charAt(0).toUpperCase() + w.slice(1))
		.join(" ");

const isRequired = (fieldName: string) =>
	schema.value?.required?.includes(fieldName) || false;

const getFieldType = (property: any, s: ConfigSchema) => {
	const r = getPropertySchema(property, s);
	if (r?.enum) return "enum";
	if (r?.type === "object" && r?.properties) return "object";
	if (r?.type === "integer" || r?.type === "number") return "number";
	if (r?.type === "string") return "string";
	if (r?.type === "boolean") return "boolean";
	return "unknown";
};

const isPasswordField = (name: string) =>
	String(name).toLowerCase().includes("password");

const isEntityField = (name: string) =>
	String(name).toLowerCase().includes("entity");

const togglePasswordVisibility = (key: string) => {
	passwordVisibility.value[key] = !passwordVisibility.value[key];
};

// ── Sensor prefix (Home Assistant entity fields) ────────────────

const SENSOR_PREFIX = "sensor.";

const isSensorEntityField = (fieldName: string) =>
	props.sensorPrefix && isEntityField(fieldName);

const getEntityDisplayValue = (fieldName: string): string => {
	const val = config.value[fieldName] ?? "";
	return String(val).startsWith(SENSOR_PREFIX)
		? String(val).slice(SENSOR_PREFIX.length)
		: String(val);
};

const setEntityValue = (fieldName: string, displayValue: string) => {
	config.value[fieldName] = displayValue ? SENSOR_PREFIX + displayValue : "";
};

const getNestedEntityDisplayValue = (
	parentKey: string,
	nestedKey: string
): string => {
	const val = config.value[parentKey]?.[nestedKey] ?? "";
	return String(val).startsWith(SENSOR_PREFIX)
		? String(val).slice(SENSOR_PREFIX.length)
		: String(val);
};

const setNestedEntityValue = (
	parentKey: string,
	nestedKey: string,
	displayValue: string
) => {
	if (config.value[parentKey]) {
		config.value[parentKey][nestedKey] = displayValue
			? SENSOR_PREFIX + displayValue
			: "";
	}
};

const onEntityInput = (fieldName: string, event: Event) => {
	setEntityValue(fieldName, (event.target as HTMLInputElement).value);
};

const onNestedEntityInput = (
	parentKey: string,
	nestedKey: string,
	event: Event
) => {
	setNestedEntityValue(
		parentKey,
		nestedKey,
		(event.target as HTMLInputElement).value
	);
};
</script>

<template>
	<div v-if="loading" class="flex items-center justify-center p-4">
		<span class="loading loading-spinner loading-md"></span>
	</div>
	<div v-else-if="schema && schema.properties" class="flex flex-col gap-3">
		<div
			v-for="(property, fieldName) in schema.properties"
			:key="fieldName"
			class="space-y-1"
		>
			<!-- Field label -->
			<div class="font-medium">
				{{ property.title || formatFieldName(String(fieldName)) }}
				<span v-if="isRequired(String(fieldName))" class="text-sm text-error opacity-60 ml-1 font-normal">(required)</span>
				<span v-if="!isRequired(String(fieldName))" class="text-sm opacity-60 ml-1 font-normal">(optional)</span>
			</div>

			<!-- Enum -->
			<select
				v-if="getFieldType(property, schema) === 'enum'"
				v-model="config[fieldName]"
				:required="isRequired(String(fieldName))"
				class="select select-bordered select-sm w-full"
			>
				<option v-if="isNullable(property)" :value="null">-- None --</option>
				<option
					v-for="option in getPropertySchema(property, schema).enum"
					:key="option"
					:value="option"
				>{{ option }}</option>
			</select>

			<!-- Object (nested) -->
			<div
				v-else-if="getFieldType(property, schema) === 'object'"
				class="border border-base-300 rounded-lg p-3 space-y-3"
			>
				<div
					v-for="(nestedProp, nestedKey) in getPropertySchema(property, schema).properties"
					:key="nestedKey"
					class="space-y-1"
				>
					<div class="font-medium text-sm">
						{{ nestedProp.title || formatFieldName(String(nestedKey)) }}
					</div>

					<!-- Nested sensor entity -->
					<div
						v-if="nestedProp.type === 'string' && isSensorEntityField(String(nestedKey))"
						class="join w-full"
					>
						<span class="join-item flex items-center px-2 bg-base-200 border border-base-300 text-xs opacity-70 select-none">sensor.</span>
						<input
							:value="getNestedEntityDisplayValue(String(fieldName), String(nestedKey))"
							@input="onNestedEntityInput(String(fieldName), String(nestedKey), $event)"
							type="text"
							placeholder="entity_id"
							class="input input-bordered input-xs join-item flex-1"
						/>
					</div>

					<!-- Nested string -->
					<div v-else-if="nestedProp.type === 'string'" class="relative">
						<input
							v-model="config[fieldName][nestedKey]"
							:type="isPasswordField(String(nestedKey)) && !passwordVisibility[String(fieldName) + '.' + String(nestedKey)] ? 'password' : 'text'"
							:placeholder="nestedProp.default || ''"
							class="input input-bordered input-xs w-full"
							:class="{ 'pr-10': isPasswordField(String(nestedKey)) }"
						/>
						<button
							v-if="isPasswordField(String(nestedKey))"
							type="button"
							@click="togglePasswordVisibility(String(fieldName) + '.' + String(nestedKey))"
							class="absolute right-2 top-1/2 -translate-y-1/2 btn btn-ghost btn-xs"
							tabindex="-1"
						>
							<PhEyeSlash v-if="passwordVisibility[String(fieldName) + '.' + String(nestedKey)]" :size="16" />
							<PhEye v-else :size="16" />
						</button>
					</div>

					<!-- Nested number -->
					<input
						v-else-if="nestedProp.type === 'number' || nestedProp.type === 'integer'"
						v-model.number="config[fieldName][nestedKey]"
						type="number"
						:step="nestedProp.type === 'integer' ? '1' : 'any'"
						:min="nestedProp.minimum"
						:max="nestedProp.maximum"
						:placeholder="nestedProp.default || ''"
						class="input input-bordered input-xs w-full"
					/>

					<div v-if="nestedProp.description" class="text-xs italic opacity-70">
						{{ nestedProp.description }}
					</div>
				</div>
			</div>

			<!-- String with sensor prefix -->
			<div
				v-else-if="getFieldType(property, schema) === 'string' && isSensorEntityField(String(fieldName))"
				class="join w-full"
			>
				<span class="join-item flex items-center px-3 bg-base-200 border border-base-300 text-sm opacity-70 select-none">sensor.</span>
				<input
					:value="getEntityDisplayValue(String(fieldName))"
					@input="onEntityInput(String(fieldName), $event)"
					type="text"
					placeholder="entity_id"
					:required="isRequired(String(fieldName))"
					class="input input-bordered input-sm join-item flex-1"
				/>
			</div>

			<!-- String -->
			<div
				v-else-if="getFieldType(property, schema) === 'string'"
				class="relative"
			>
				<input
					v-model="config[fieldName]"
					:type="isPasswordField(String(fieldName)) && !passwordVisibility[String(fieldName)] ? 'password' : 'text'"
					:placeholder="property.default || ''"
					:required="isRequired(String(fieldName))"
					class="input input-bordered input-sm w-full"
					:class="{ 'pr-10': isPasswordField(String(fieldName)) }"
				/>
				<button
					v-if="isPasswordField(String(fieldName))"
					type="button"
					@click="togglePasswordVisibility(String(fieldName))"
					class="absolute right-2 top-1/2 -translate-y-1/2 btn btn-ghost btn-xs"
					tabindex="-1"
				>
					<PhEyeSlash v-if="passwordVisibility[String(fieldName)]" :size="16" />
					<PhEye v-else :size="16" />
				</button>
			</div>

			<!-- Number -->
			<input
				v-else-if="getFieldType(property, schema) === 'number'"
				v-model.number="config[fieldName]"
				type="number"
				:step="getPropertySchema(property, schema).type === 'integer' ? '1' : 'any'"
				:min="getPropertySchema(property, schema).minimum"
				:max="getPropertySchema(property, schema).maximum"
				:placeholder="property.default"
				:required="isRequired(String(fieldName))"
				class="input input-bordered input-sm w-full"
			/>

			<!-- Boolean -->
			<label
				v-else-if="getFieldType(property, schema) === 'boolean'"
				class="flex items-center gap-2 cursor-pointer"
			>
				<input
					v-model="config[fieldName]"
					type="checkbox"
					class="checkbox checkbox-sm"
				/>
				<span class="text-sm">{{ property.description || "Enable" }}</span>
			</label>

			<!-- Description -->
			<div
				v-if="property.description &&
					getFieldType(property, schema) !== 'boolean' &&
					getFieldType(property, schema) !== 'object'"
				class="text-sm italic opacity-70"
			>
				{{ property.description }}
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
import type {
	ConfigSchema,
	ForecastProviderConfig,
} from "../../core/models/forecastProvider";
import { ForecastProviderService } from "../../core/services/forecastProviderService";

const props = defineProps<{
	adapterType: string;
}>();

const config = defineModel<ForecastProviderConfig>({ required: true });

const service = new ForecastProviderService();
const schema = ref<ConfigSchema | null>(null);
const loading = ref(false);
const passwordVisibility = ref<Record<string, boolean>>({});

// Resolve $ref to actual schema definition
const resolveRef = (ref: string, schema: ConfigSchema): any => {
	if (!ref.startsWith("#/$defs/")) return null;
	const defName = ref.replace("#/$defs/", "");
	return schema.$defs?.[defName] || null;
};

// Get resolved property schema (handling $ref and anyOf)
const getPropertySchema = (property: any, schema: ConfigSchema): any => {
	if (property.$ref) {
		return resolveRef(property.$ref, schema);
	}

	// Handle anyOf (find first non-null type)
	if (property.anyOf) {
		const nonNullType = property.anyOf.find((item: any) => item.type !== "null");
		if (nonNullType) {
			// If it's a $ref, resolve it
			if (nonNullType.$ref) {
				return resolveRef(nonNullType.$ref, schema);
			}
			// Merge anyOf type with parent property (preserving default, description, etc.)
			return { ...property, ...nonNullType, anyOf: undefined };
		}
	}

	return property;
};

// Check if property is nullable (has anyOf with null type)
const isNullable = (property: any): boolean => {
	if (property.anyOf) {
		return property.anyOf.some((item: any) => item.type === "null");
	}
	return false;
};

// Initialize default value based on property schema
const initializeDefaultValue = (property: any, schema: ConfigSchema): any => {
	// Check if property has explicit default
	if (property.default !== undefined) {
		return property.default;
	}

	// Resolve $ref and anyOf if present
	const resolvedProperty = getPropertySchema(property, schema);

	// Check default in resolved property
	if (resolvedProperty?.default !== undefined) {
		return resolvedProperty.default;
	}

	// If nullable and no default, return null
	if (isNullable(property)) {
		return null;
	}

	// Handle enum
	if (resolvedProperty?.enum) {
		return resolvedProperty.enum[0];
	}

	// Handle object type
	if (resolvedProperty?.type === "object" && resolvedProperty?.properties) {
		const obj: any = {};
		Object.entries(resolvedProperty.properties).forEach(([key, prop]: [string, any]) => {
			obj[key] = initializeDefaultValue(prop, schema);
		});
		return obj;
	}

	// Handle primitive types
	if (resolvedProperty?.type === "string") return "";
	if (resolvedProperty?.type === "number" || resolvedProperty?.type === "integer") return 0;
	if (resolvedProperty?.type === "boolean") return false;

	return null;
};

// Load schema when adapter type changes
watch(
	() => props.adapterType,
	async (newAdapterType) => {
		if (!newAdapterType) {
			schema.value = null;
			return;
		}

		loading.value = true;
		try {
			schema.value = await service.getConfigSchema(newAdapterType);

			// Initialize config with default values, preserving existing values
			if (schema.value?.properties) {
				const existingConfig = { ...config.value };
				const newConfig: ForecastProviderConfig = {} as any;
				Object.entries(schema.value.properties).forEach(([key, property]) => {
					if (existingConfig[key] !== undefined) {
						newConfig[key] = existingConfig[key];
					} else {
						newConfig[key] = initializeDefaultValue(property, schema.value!);
					}
				});
				config.value = newConfig;
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

// Format field name for display
const formatFieldName = (name: string) => {
	return name
		.split("_")
		.map((word) => word.charAt(0).toUpperCase() + word.slice(1))
		.join(" ");
};

// Check if field is required
const isRequired = (fieldName: string) => {
	return schema.value?.required?.includes(fieldName) || false;
};

// Get field type for rendering
const getFieldType = (property: any, schema: ConfigSchema) => {
	const resolvedProp = getPropertySchema(property, schema);

	if (resolvedProp?.enum) return 'enum';
	if (resolvedProp?.type === 'object' && resolvedProp?.properties) return 'object';
	if (resolvedProp?.type === 'integer' || resolvedProp?.type === 'number') return 'number';
	if (resolvedProp?.type === 'string') return 'string';
	if (resolvedProp?.type === 'boolean') return 'boolean';

	return 'unknown';
};

// Toggle password visibility
const togglePasswordVisibility = (fieldKey: string) => {
	passwordVisibility.value[fieldKey] = !passwordVisibility.value[fieldKey];
};

// Check if field is a password field
const isPasswordField = (fieldName: string): boolean => {
	return String(fieldName).toLowerCase().includes('password');
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
			<!-- Field label with required/optional indicator -->
			<div class="font-medium">
				{{ property.title || formatFieldName(String(fieldName)) }}
				<span v-if="isRequired(String(fieldName))" class="text-sm text-error opacity-60 ml-1 font-normal">(required)</span>
				<span v-if="!isRequired(String(fieldName))" class="text-sm opacity-60 ml-1 font-normal">(optional)</span>
			</div>

			<!-- Enum select -->
			<select
				v-if="getFieldType(property, schema) === 'enum'"
				v-model="config[fieldName]"
				:required="isRequired(String(fieldName))"
				class="select select-bordered select-sm w-full"
			>
				<option v-if="isNullable(property)" :value="null">
					-- None --
				</option>
				<option
					v-for="option in getPropertySchema(property, schema).enum"
					:key="option"
					:value="option"
				>
					{{ option }}
				</option>
			</select>

			<!-- Object type (nested properties) -->
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
          
					<!-- Nested string -->
					<div
						v-if="nestedProp.type === 'string'"
						class="relative"
					>
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
          
					<!-- Nested description -->
					<div v-if="nestedProp.description" class="text-xs italic opacity-70">
						{{ nestedProp.description }}
					</div>
				</div>
			</div>

			<!-- String input -->
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

			<!-- Number input -->
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

			<!-- Boolean checkbox -->
			<label 
				v-else-if="getFieldType(property, schema) === 'boolean'" 
				class="flex items-center gap-2 cursor-pointer"
			>
				<input
					v-model="config[fieldName]"
					type="checkbox"
					class="checkbox checkbox-sm"
				/>
				<span class="text-sm">
					{{ property.description || 'Enable' }}
				</span>
			</label>

			<!-- Description helper text -->
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

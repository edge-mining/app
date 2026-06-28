<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { BaseService } from "../core/services/baseService";
import ConfigFieldControl from "./ConfigFieldControl.vue";
import {
	type ConfigSchema,
	type ConfigSchemaProperty,
	formatFieldName,
	initializeDefaultValue,
	isEntityField,
} from "../core/utils/configSchema";

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

// ── Form layout (issue #17) ─────────────────────────────────────
//
// Fields are reorganized for readability:
//  - each "entity_<x>" field is paired with its "unit_<x>" field on the
//    same row, so the value and its unit of measure stay together;
//  - rows are grouped by domain (Power / Energy / Hash Rate) when at least
//    two domains are present, otherwise rendered as a single flat list;
//  - the original schema declaration order is preserved within each group.

interface LayoutCell {
	name: string;
	property: ConfigSchemaProperty;
}
interface LayoutRow {
	key: string;
	cells: LayoutCell[];
}
interface LayoutGroup {
	label: string | null;
	rows: LayoutRow[];
}

const DOMAIN_ORDER = ["power", "energy", "hashrate"];
const DOMAIN_LABELS: Record<string, string> = {
	power: "Power",
	energy: "Energy",
	hashrate: "Hash Rate",
};
const OTHER_KEY = "__other__";

const detectDomain = (name: string): string | null => {
	const n = name.toLowerCase();
	if (n.includes("hash")) return "hashrate";
	if (n.includes("power")) return "power";
	if (n.includes("energy")) return "energy";
	return null;
};

const isRequired = (fieldName: string) =>
	schema.value?.required?.includes(fieldName) || false;

const layout = computed<LayoutGroup[]>(() => {
	const s = schema.value;
	if (!s?.properties) return [];

	const entries = Object.entries(s.properties);
	const propMap = new Map(entries);
	const consumed = new Set<string>();
	const rows: { row: LayoutRow; domain: string | null }[] = [];

	for (const [name, property] of entries) {
		if (consumed.has(name)) continue;
		consumed.add(name);

		const cells: LayoutCell[] = [{ name, property }];

		// Pair "entity_<x>" with its "unit_<x>" counterpart on the same row.
		if (isEntityField(name) && name.startsWith("entity_")) {
			const unitName = `unit_${name.slice("entity_".length)}`;
			const unitProp = propMap.get(unitName);
			if (unitProp && !consumed.has(unitName)) {
				cells.push({ name: unitName, property: unitProp });
				consumed.add(unitName);
			}
		}

		rows.push({ row: { key: name, cells }, domain: detectDomain(name) });
	}

	// Group by domain only when there are at least two distinct domains.
	const domains = new Set(
		rows.map((r) => r.domain).filter((d): d is string => d !== null)
	);
	if (domains.size < 2) {
		return [{ label: null, rows: rows.map((r) => r.row) }];
	}

	const buckets = new Map<string, LayoutRow[]>();
	for (const { row, domain } of rows) {
		const key = domain ?? OTHER_KEY;
		if (!buckets.has(key)) buckets.set(key, []);
		buckets.get(key)!.push(row);
	}

	const orderedKeys = [
		...DOMAIN_ORDER.filter((d) => buckets.has(d)),
		...[...buckets.keys()].filter(
			(k) => !DOMAIN_ORDER.includes(k) && k !== OTHER_KEY
		),
		...(buckets.has(OTHER_KEY) ? [OTHER_KEY] : []),
	];

	return orderedKeys.map((k) => ({
		label: k === OTHER_KEY ? "Other" : DOMAIN_LABELS[k] ?? formatFieldName(k),
		rows: buckets.get(k)!,
	}));
});

const cellClass = (row: LayoutRow, index: number): string => {
	if (row.cells.length === 1) return "w-full";
	return index === 0 ? "flex-1 min-w-0" : "sm:shrink-0";
};
</script>

<template>
	<div v-if="loading" class="flex items-center justify-center p-4">
		<span class="loading loading-spinner loading-md"></span>
	</div>
	<div v-else-if="schema && schema.properties" class="flex flex-col gap-4">
		<div v-for="(group, gi) in layout" :key="gi" class="flex flex-col gap-3">
			<div
				v-if="group.label"
				class="text-xs font-semibold uppercase tracking-wide opacity-60 border-b border-base-300/40 pb-1"
			>
				{{ group.label }}
			</div>

			<div
				v-for="row in group.rows"
				:key="row.key"
				class="flex flex-col sm:flex-row sm:items-start gap-3"
			>
				<div
					v-for="(cell, ci) in row.cells"
					:key="cell.name"
					:class="cellClass(row, ci)"
				>
					<ConfigFieldControl
						v-model="config[cell.name]"
						:name="cell.name"
						:property="cell.property"
						:schema="schema"
						:required="isRequired(cell.name)"
						:sensor-prefix="sensorPrefix"
					/>
				</div>
			</div>
		</div>
	</div>
</template>

/**
 * Shared helpers for the dynamic configuration forms generated from a
 * JSON schema (see ConfigSchemaForm.vue / ConfigFieldControl.vue).
 */

export interface ConfigSchemaProperty {
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

export interface ConfigSchema {
	title?: string;
	description?: string;
	type?: string;
	properties: Record<string, ConfigSchemaProperty>;
	required?: string[];
	$defs?: Record<string, ConfigSchemaProperty>;
}

export type FieldType = "enum" | "object" | "number" | "string" | "boolean" | "unknown";

// ── Schema resolution ───────────────────────────────────────────

export const resolveRef = (refStr: string, s: ConfigSchema): any => {
	if (!refStr.startsWith("#/$defs/")) return null;
	return s.$defs?.[refStr.replace("#/$defs/", "")] || null;
};

export const getPropertySchema = (property: any, s: ConfigSchema): any => {
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

export const isNullable = (property: any): boolean =>
	!!property.anyOf?.some((i: any) => i.type === "null");

export const getFieldType = (property: any, s: ConfigSchema): FieldType => {
	const r = getPropertySchema(property, s);
	if (r?.enum) return "enum";
	if (r?.type === "object" && r?.properties) return "object";
	if (r?.type === "integer" || r?.type === "number") return "number";
	if (r?.type === "string") return "string";
	if (r?.type === "boolean") return "boolean";
	return "unknown";
};

export const initializeDefaultValue = (property: any, s: ConfigSchema): any => {
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

// ── Field name helpers ──────────────────────────────────────────

export const formatFieldName = (name: string): string =>
	name
		.split("_")
		.map((w) => w.charAt(0).toUpperCase() + w.slice(1))
		.join(" ");

export const isPasswordField = (name: string): boolean =>
	String(name).toLowerCase().includes("password");

export const isEntityField = (name: string): boolean =>
	String(name).toLowerCase().includes("entity");

export const isUnitField = (name: string): boolean =>
	String(name).toLowerCase().includes("unit");

// ── Measurement unit registry (issue #18) ───────────────────────
//
// Unit fields are rendered as a segmented control instead of a free-text
// input. The set of options is inferred from the field's value family,
// detected primarily from its current/default value (most reliable) and,
// as a fallback, from keywords in the field name.

interface UnitFamily {
	key: string;
	/** Canonical, selectable options shown in the segmented control. */
	options: string[];
	/** Extra recognized values (used only to detect the family, not shown). */
	aliases: string[];
	/** Keywords in the field name that hint at this family. */
	keywords: string[];
}

const UNIT_FAMILIES: UnitFamily[] = [
	{ key: "power", options: ["W", "kW", "MW"], aliases: ["GW"], keywords: ["power"] },
	{ key: "energy", options: ["Wh", "kWh", "MWh"], aliases: ["GWh"], keywords: ["energy", "capacity"] },
	{
		key: "hashrate",
		options: ["GH/s", "TH/s", "PH/s"],
		aliases: ["H/s", "KH/s", "MH/s", "EH/s"],
		keywords: ["hash"],
	},
];

const familyFromValue = (value: unknown): UnitFamily | undefined => {
	if (typeof value !== "string" || value === "") return undefined;
	const v = value.toLowerCase();
	return UNIT_FAMILIES.find((f) =>
		[...f.options, ...f.aliases].some((u) => u.toLowerCase() === v)
	);
};

const familyFromName = (name: string): UnitFamily | undefined => {
	const n = name.toLowerCase();
	return UNIT_FAMILIES.find((f) => f.keywords.some((k) => n.includes(k)));
};

/**
 * Returns the list of selectable unit options for a unit field, or `null`
 * if the field is not a unit field or its family cannot be determined
 * (in which case the caller should fall back to a plain text input).
 *
 * The current value is always included so no previously-saved custom value
 * is lost.
 */
export const getUnitOptions = (
	name: string,
	property: ConfigSchemaProperty,
	currentValue: unknown
): string[] | null => {
	if (!isUnitField(name)) return null;

	const family =
		familyFromValue(currentValue) ??
		familyFromValue(property.default) ??
		familyFromName(name);

	if (!family) return null;

	const options = [...family.options];
	if (typeof currentValue === "string" && currentValue && !options.includes(currentValue)) {
		options.push(currentValue);
	}
	return options;
};

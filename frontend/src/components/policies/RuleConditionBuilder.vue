<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue';
import { useRuleEngineStore } from '../../core/stores/ruleEngineStore';
import { usePolicyStore } from '../../core/stores/policyStore';
import type { RuleConditions, RuleCondition, LogicalGroup, RuleValidationResult, OperatorType } from '../../core/models/ruleEngine';
import type { DecisionalContextField } from '../../core/models/policy';
import { OPERATOR_SYMBOLS } from '../../core/models/ruleEngine';
import { PhCheckCircle, PhXCircle, PhCheck, PhX, PhFloppyDisk, PhLock, PhLockOpen, PhInfo, PhPlus, PhWarning, PhCaretDown, PhListMagnifyingGlass, PhTree, PhGraph, PhBracketsAngle } from '@phosphor-icons/vue';
import RuleConditionGraph from './RuleConditionGraph.vue';
import JsonEditor from './JsonEditor.vue';

interface Props {
  modelValue?: RuleConditions;
  depth?: number;
  godMode?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: () => ({} as LogicalGroup),
  depth: 0,
  godMode: false
});

const emit = defineEmits<{
  (e: 'update:modelValue', value: RuleConditions): void;
}>();

const ruleEngineStore = useRuleEngineStore();
const policyStore = usePolicyStore();

// Load decisional context structure on mount
onMounted(async () => {
  if (useLocalState.value) {
    localValue.value = JSON.parse(JSON.stringify(props.modelValue));
    // Load context structure if not already loaded
    if (!policyStore.decisionalContextStructure) {
      try {
        await policyStore.loadDecisionalContextStructure();
      } catch (error) {
        console.error('Failed to load decisional context structure:', error);
      }
    }
  }
});

// God mode toggle (only at root level)
const godMode = ref(false);

// Only use local editing state at root level (depth === 0)
const useLocalState = computed(() => props.depth === 0);

// Local editing state (only for root level)
const localValue = ref<RuleConditions>(JSON.parse(JSON.stringify(props.modelValue)));
const originalValue = ref<RuleConditions>(JSON.parse(JSON.stringify(props.modelValue)));
const hasChanges = ref(false);

// Check if current conditions differ from the original (props)
const hasUnsavedChanges = computed(() => {
  if (!useLocalState.value) return false;
  return JSON.stringify(props.modelValue) !== JSON.stringify(localValue.value);
});

// Get the current working value (local if root, props if nested)
const workingValue = computed(() => {
  return useLocalState.value ? localValue.value : props.modelValue;
});

// Field selector state
const showFieldSelector = ref<number | null>(null);
const fieldSearchQuery = ref('');

// Get all available fields from decisional context structure
const availableFields = computed(() => {
  if (!policyStore.decisionalContextStructure) return [];

  const flattenFields = (fields: DecisionalContextField[]): DecisionalContextField[] => {
    const result: DecisionalContextField[] = [];
    for (const field of fields) {
      result.push(field);
      if (field.children && field.children.length > 0) {
        result.push(...flattenFields(field.children));
      }
    }
    return result;
  };

  return flattenFields(policyStore.decisionalContextStructure.fields);
});

// Filter fields by search query
const filteredFields = computed(() => {
  if (!fieldSearchQuery.value) return availableFields.value;

  const query = fieldSearchQuery.value.toLowerCase();
  return availableFields.value.filter(field =>
    field.path.toLowerCase().includes(query) ||
    field.description.toLowerCase().includes(query) ||
    field.type.toLowerCase().includes(query)
  );
});

// Group fields by root level (first part of path)
const groupedFields = computed(() => {
  const groups: Record<string, DecisionalContextField[]> = {};

  for (const field of filteredFields.value) {
    const rootPath = field.path.split('.')[0];
    if (!groups[rootPath]) {
      groups[rootPath] = [];
    }
    groups[rootPath].push(field);
  }

  return groups;
});

// Get field info by path
const getFieldInfo = (path: string): DecisionalContextField | undefined => {
  return availableFields.value.find(f => f.path === path);
};

// Initialize local value from props
onMounted(() => {
  if (useLocalState.value) {
    localValue.value = JSON.parse(JSON.stringify(props.modelValue));
    originalValue.value = JSON.parse(JSON.stringify(props.modelValue));
  }
});

// Watch for external changes to props
watch(() => props.modelValue, (newVal) => {
  if (useLocalState.value && !hasChanges.value) {
    localValue.value = JSON.parse(JSON.stringify(newVal));
    originalValue.value = JSON.parse(JSON.stringify(newVal));
  }
}, { deep: true });

// Save changes (only at root level)
const saveChanges = () => {
  if (useLocalState.value) {
    emit('update:modelValue', JSON.parse(JSON.stringify(localValue.value)));
    hasChanges.value = false;
    validateConditions();
  }
};

// Cancel changes (only at root level)
const cancelChanges = () => {
  if (useLocalState.value) {
    localValue.value = JSON.parse(JSON.stringify(props.modelValue));
    hasChanges.value = false;
    validationResult.value = null;
  }
};

// Restore to original conditions from the rule (only at root level)
const restoreOriginal = () => {
  if (useLocalState.value) {
    localValue.value = JSON.parse(JSON.stringify(originalValue.value));
    hasChanges.value = false;
    validationResult.value = null;
  }
};

// Mark as changed (only at root level)
const markAsChanged = () => {
  if (useLocalState.value) {
    hasChanges.value = true;
  }
};

// Update working value
const updateWorkingValue = (newValue: RuleConditions) => {
  if (useLocalState.value) {
    localValue.value = newValue;
    markAsChanged();
  } else {
    emit('update:modelValue', newValue);
  }
};

// View mode toggle
const viewMode = ref<'builder' | 'json' | 'graph'>('builder');

// JSON string for editing
const jsonString = ref(JSON.stringify(localValue.value, null, 2));

// Validation state
const validationResult = ref<RuleValidationResult | null>(null);
const isValidating = ref(false);

// Update rule from JSON
const updateFromJson = () => {
  try {
    updateWorkingValue(JSON.parse(jsonString.value));
  } catch (e) {
    console.error('Invalid JSON:', e);
  }
};

// Update JSON from rule
const updateJson = () => {
  jsonString.value = JSON.stringify(workingValue.value, null, 2);
};

// Validate conditions using rule engine
const validateConditions = async () => {
  if (props.depth !== 0) return; // Only validate at root level

  isValidating.value = true;
  try {
    const result = await ruleEngineStore.validate({
      conditions: workingValue.value as RuleCondition | LogicalGroup
    });
    validationResult.value = result;
  } catch (error) {
    console.error('Validation error:', error);
    validationResult.value = {
      is_valid: false,
      validation_errors: ['Failed to validate conditions'],
      syntax_errors: [],
      field_errors: []
    };
  } finally {
    isValidating.value = false;
  }
};

// Available operators - mapped from OPERATOR_SYMBOLS
const operators = [
  { value: 'eq' as OperatorType, label: `Equal ${OPERATOR_SYMBOLS.eq}`, description: 'Equal to' },
  { value: 'ne' as OperatorType, label: `Not Equal ${OPERATOR_SYMBOLS.ne}`, description: 'Not equal to' },
  { value: 'gt' as OperatorType, label: `Greater Than ${OPERATOR_SYMBOLS.gt}`, description: 'Greater than' },
  { value: 'gte' as OperatorType, label: `Greater or Equal ${OPERATOR_SYMBOLS.gte}`, description: 'Greater than or equal to' },
  { value: 'lt' as OperatorType, label: `Less Than ${OPERATOR_SYMBOLS.lt}`, description: 'Less than' },
  { value: 'lte' as OperatorType, label: `Less or Equal ${OPERATOR_SYMBOLS.lte}`, description: 'Less than or equal to' },
  { value: 'in' as OperatorType, label: `In ${OPERATOR_SYMBOLS.in}`, description: 'Value is in list' },
  { value: 'not_in' as OperatorType, label: `Not In ${OPERATOR_SYMBOLS.not_in}`, description: 'Value is not in list' },
  { value: 'contains' as OperatorType, label: `Contains ${OPERATOR_SYMBOLS.contains}`, description: 'String contains substring' },
  { value: 'starts_with' as OperatorType, label: `Starts With ${OPERATOR_SYMBOLS.starts_with}`, description: 'String starts with' },
  { value: 'ends_with' as OperatorType, label: `Ends With ${OPERATOR_SYMBOLS.ends_with}`, description: 'String ends with' },
  { value: 'regex' as OperatorType, label: `Regex ${OPERATOR_SYMBOLS.regex}`, description: 'Matches regular expression' },
];

// Common field suggestions
const fieldSuggestions = computed(() => {
  // Return frequently used fields from the structure
  return availableFields.value
    .filter(f => !f.children || f.children.length === 0) // Only leaf nodes
    .slice(0, 20)
    .map(f => f.path);
});

// Default rule templates
const defaultAllOfRule: LogicalGroup = {
  all_of: [
    { field: 'energy_state.production', operator: 'gt', value: 100 },
    { field: 'energy_state.battery.state_of_charge', operator: 'gte', value: 80 },
    { field: 'price.electricity', operator: 'lt', value: 0.15 }
  ]
};

const defaultAnyOfRule: LogicalGroup = {
  any_of: [
    { field: 'energy_state.production', operator: 'lt', value: 50 },
    { field: 'energy_state.battery.state_of_charge', operator: 'lte', value: 20 },
    { field: 'price.electricity', operator: 'gt', value: 0.25 }
  ]
};

const defaultNotRule: LogicalGroup = {
  not_: { field: 'miner.hashrate', operator: 'eq', value: 0 }
};

// Check if rule condition is a group
const isGroup = (ruleCondition: RuleConditions): ruleCondition is LogicalGroup => {
  return ruleCondition !== null && typeof ruleCondition === 'object' && ('any_of' in ruleCondition || 'all_of' in ruleCondition || 'not_' in ruleCondition);
};

// Check if ruleCondition is a condition
const isCondition = (ruleCondition: RuleConditions): ruleCondition is RuleCondition => {
  return ruleCondition !== null && typeof ruleCondition === 'object' && 'field' in ruleCondition && 'operator' in ruleCondition && ('value' in ruleCondition || 'value_ref' in ruleCondition);
};

// Check if ruleCondition is empty (no properties)
const isEmpty = (ruleCondition: RuleConditions): boolean => {
  return ruleCondition !== null && typeof ruleCondition === 'object' && Object.keys(ruleCondition).length === 0;
};

// Get group type
const groupType = computed(() => {
  if (isGroup(workingValue.value)) {
    if ('not_' in workingValue.value) return 'not_';
    return 'any_of' in workingValue.value ? 'any_of' : 'all_of';
  }
  return null;
});

// Get group items
const groupItems = computed(() => {
  if (isGroup(workingValue.value)) {
    const type = groupType.value as 'any_of' | 'all_of' | 'not_';
    if (type === 'not_') {
      // not_ contains a single item, not an array
      const notItem = workingValue.value.not_;
      return notItem ? [notItem] : [];
    }
    return workingValue.value[type] || [];
  }
  return [];
});

// Check if god mode is enabled (for nested components, inherit from parent)
const isGodModeEnabled = computed(() => {
  return props.depth === 0 ? godMode.value : props.godMode;
});

// Update condition field
const updateConditionField = (field: keyof RuleCondition, value: any) => {
  if (isCondition(workingValue.value)) {
    updateWorkingValue({
      ...workingValue.value,
      [field]: value
    });
  }
};

// Update group item
const updateGroupItem = (index: number, newValue: RuleConditions) => {
  if (isGroup(workingValue.value)) {
    const type = groupType.value as 'any_of' | 'all_of' | 'not_';
    if (type === 'not_') {
      // not_ contains a single item, not an array
      if (!isGroup(newValue) && !isCondition(newValue)) {
        console.error('Invalid value for not_ group');
        return;
      }
      updateWorkingValue({
        not_: newValue
      });
    } else {
      const items = [...(workingValue.value[type] || [])];
      if (!isGroup(newValue) && !isCondition(newValue)) {
        console.error('Invalid value for group item');
        return;
      }
      items[index] = newValue;
      updateWorkingValue({
        [type]: items
      });
    }
  }
};

// Add condition to group
const addCondition = () => {
  if (isGroup(workingValue.value)) {
    const type = groupType.value as 'any_of' | 'all_of' | 'not_';
    if (type === 'not_') {
      // not_ can only contain one item, so replace it
      updateWorkingValue({
        not_: {
          field: '',
          operator: 'eq' as OperatorType,
          value: ''
        }
      });
    } else {
      const items = [...(workingValue.value[type] || [])];
      items.push({
        field: '',
        operator: 'eq' as OperatorType,
        value: ''
      });
      updateWorkingValue({
        [type]: items
      });
    }
  }
};

// Add group to group
const addGroup = (type: 'any_of' | 'all_of' | 'not_') => {
  if (isGroup(workingValue.value)) {
    const currentType = groupType.value as 'any_of' | 'all_of' | 'not_';

    const newGroup = type === 'not_'
      ? {
          [type]: {
            field: '',
            operator: 'eq' as OperatorType,
            value: ''
          }
        }
      : {
          [type]: [
            {
              field: '',
              operator: 'eq' as OperatorType,
              value: ''
            }
          ]
        };

    if (currentType === 'not_') {
      // not_ can only contain one item, so replace it
      updateWorkingValue(newGroup);
    } else {
      const items = [...(workingValue.value[currentType] || [])];
      items.push(newGroup);
      updateWorkingValue({
        [currentType]: items
      });
    }
  }
};

// Remove item from group
const removeItem = (index: number) => {
  if (isGroup(workingValue.value)) {
    const type = groupType.value as 'any_of' | 'all_of' | 'not_';
    if (type === 'not_') {
      // Can't remove the only item from not_, should be disabled in UI
      return;
    }
    const items = [...(workingValue.value[type] || [])];
    items.splice(index, 1);
    updateWorkingValue({
      [type]: items
    });
  }
};

// Toggle group type (any_of <-> all_of <-> not_)
const toggleGroupType = (event?: Event) => {
  if (event) {
    event.preventDefault();
    event.stopPropagation();
    event.stopImmediatePropagation();
  }

  if (isGroup(workingValue.value)) {
    const currentType = groupType.value as 'any_of' | 'all_of' | 'not_';
    // Cycle: any_of -> all_of -> not_ -> any_of
    let newType: 'any_of' | 'all_of' | 'not_';
    if (currentType === 'any_of') newType = 'all_of';
    else if (currentType === 'all_of') newType = 'not_';
    else newType = 'any_of';

    // Preserve content but change group type
    if (currentType === 'not_') {
      // Converting from not_ (single item) to any_of/all_of (array)
      const item = workingValue.value.not_;
      updateWorkingValue({
        [newType]: item ? [item] : []
      });
    } else if (newType === 'not_') {
      // Converting to not_ (single item) from any_of/all_of (array)
      // Keep only the first item
      const items = workingValue.value[currentType] || [];
      updateWorkingValue({
        not_: items.length > 0 ? items[0] : { field: '', operator: 'eq' as OperatorType, value: '' }
      });
    } else {
      // Converting between any_of and all_of (both arrays) - preserve all items
      const items = workingValue.value[currentType] || [];
      updateWorkingValue({
        [newType]: items
      });
    }
  }
};

// Parse value based on type
const parseValue = (val: string, operator: OperatorType): string | number | boolean | Array<number | string> => {
  // For array operators (in, not_in), try to parse as JSON array
  if (operator === 'in' || operator === 'not_in') {
    try {
      const parsed = JSON.parse(val);
      if (Array.isArray(parsed)) {
        return parsed;
      }
    } catch (e) {
      // If not valid JSON, try to split by comma
      if (val.includes(',')) {
        return val.split(',').map(v => {
          const trimmed = v.trim();
          if (!isNaN(Number(trimmed)) && trimmed !== '') {
            return Number(trimmed);
          }
          return trimmed;
        });
      }
    }
  }

  // Try to parse as number
  if (!isNaN(Number(val)) && val !== '') {
    return Number(val);
  }
  // Try to parse as boolean
  if (val === 'true') return true;
  if (val === 'false') return false;
  // Return as string
  return val;
};

// Helper methods for input handling
const dropdownButtonRef = ref<HTMLElement | null>(null);
const fieldDropdownRef = ref<HTMLElement | null>(null);

// Add menu state (teleported to escape modal overflow clipping)
const showAddMenu = ref(false);
const addMenuBtnRef = ref<HTMLElement | null>(null);
const addMenuPosition = ref({ top: '0px', left: '0px' });

const handleFieldSelect = (path: string) => {
  if (isCondition(workingValue.value)) {
    updateConditionField('field', path);
  }

  // Always close selector after selection
  showFieldSelector.value = null;
  fieldSearchQuery.value = '';
};

const toggleFieldSelector = (index: number | null) => {
  if (showFieldSelector.value === index) {
    showFieldSelector.value = null;
    fieldSearchQuery.value = '';
  } else {
    showFieldSelector.value = index;
    fieldSearchQuery.value = '';

    // Calculate dropdown position with smart direction (above/below)
    setTimeout(() => {
      if (dropdownButtonRef.value) {
        const rect = dropdownButtonRef.value.getBoundingClientRect();
        const estimatedDropdownHeight = 560; // max-h-[500px] + header/search
        const spaceBelow = window.innerHeight - rect.bottom - 8;
        const spaceAbove = rect.top - 8;

        let top: number;
        if (spaceBelow >= estimatedDropdownHeight) {
          top = rect.bottom + 4;
        } else if (spaceAbove > spaceBelow) {
          top = Math.max(4, rect.top - estimatedDropdownHeight);
        } else {
          top = rect.bottom + 4;
        }

        document.documentElement.style.setProperty('--dropdown-top', `${top}px`);
        document.documentElement.style.setProperty('--dropdown-left', `${rect.left}px`);
      }
    }, 0);
  }
};

const handleOperatorChange = (event: Event) => {
  const target = event.target as HTMLSelectElement;
  updateConditionField('operator', target.value as OperatorType);
};

const handleValueInput = (event: Event) => {
  if (!isCondition(workingValue.value)) return;
  const target = event.target as HTMLInputElement;
  updateConditionField('value', parseValue(target.value, workingValue.value.operator));
};

// Check if a condition uses value_ref mode
const isValueRefMode = computed(() => {
  if (!isCondition(workingValue.value)) return false;
  return 'value_ref' in workingValue.value && workingValue.value.value_ref !== undefined;
});

// Toggle between static value and field reference
const toggleValueMode = () => {
  if (!isCondition(workingValue.value)) return;
  if (isValueRefMode.value) {
    // Switch from value_ref to static value
    const { value_ref, ...rest } = workingValue.value;
    updateWorkingValue({ ...rest, value: '' });
  } else {
    // Switch from static value to value_ref
    const { value, ...rest } = workingValue.value;
    updateWorkingValue({ ...rest, value_ref: '' });
  }
};

// Handle value_ref input
const handleValueRefInput = (event: Event) => {
  if (!isCondition(workingValue.value)) return;
  const target = event.target as HTMLInputElement;
  updateConditionField('value_ref', target.value);
};

// Handle value_ref field selection from dropdown
const handleValueRefFieldSelect = (path: string) => {
  if (isCondition(workingValue.value)) {
    updateConditionField('value_ref', path);
  }
  showValueRefSelector.value = null;
  valueRefSearchQuery.value = '';
};

// value_ref field selector state
const showValueRefSelector = ref<number | null>(null);
const valueRefSearchQuery = ref('');
const valueRefDropdownRef = ref<HTMLElement | null>(null);
const valueRefButtonRef = ref<HTMLElement | null>(null);

// Filter fields for value_ref selector
const filteredValueRefFields = computed(() => {
  const leafFields = availableFields.value.filter(f => !f.children || f.children.length === 0);
  if (!valueRefSearchQuery.value) return leafFields;
  const query = valueRefSearchQuery.value.toLowerCase();
  return leafFields.filter(field =>
    field.path.toLowerCase().includes(query) ||
    field.description.toLowerCase().includes(query)
  );
});

// Group value_ref fields by root
const groupedValueRefFields = computed(() => {
  const groups: Record<string, DecisionalContextField[]> = {};
  for (const field of filteredValueRefFields.value) {
    const rootPath = field.path.split('.')[0];
    if (!groups[rootPath]) groups[rootPath] = [];
    groups[rootPath].push(field);
  }
  return groups;
});

const toggleValueRefSelector = () => {
  if (showValueRefSelector.value !== null) {
    showValueRefSelector.value = null;
    valueRefSearchQuery.value = '';
  } else {
    showValueRefSelector.value = 0;
    valueRefSearchQuery.value = '';
    setTimeout(() => {
      if (valueRefButtonRef.value) {
        const rect = valueRefButtonRef.value.getBoundingClientRect();
        const estimatedDropdownHeight = 400;
        const spaceBelow = window.innerHeight - rect.bottom - 8;
        let top: number;
        if (spaceBelow >= estimatedDropdownHeight) {
          top = rect.bottom + 4;
        } else {
          top = Math.max(4, rect.top - estimatedDropdownHeight);
        }
        document.documentElement.style.setProperty('--vref-dropdown-top', `${top}px`);
        document.documentElement.style.setProperty('--vref-dropdown-left', `${rect.left}px`);
      }
    }, 0);
  }
};

const closeValueRefSelector = () => {
  showValueRefSelector.value = null;
  valueRefSearchQuery.value = '';
};

// Close field selector when clicking outside
const closeFieldSelector = () => {
  showFieldSelector.value = null;
  fieldSearchQuery.value = '';
};

// Add menu methods
const toggleAddMenu = () => {
  if (showAddMenu.value) {
    showAddMenu.value = false;
    return;
  }
  if (addMenuBtnRef.value) {
    const rect = addMenuBtnRef.value.getBoundingClientRect();
    const menuHeight = 180;
    const spaceBelow = window.innerHeight - rect.bottom - 8;

    let top: number;
    if (spaceBelow >= menuHeight) {
      top = rect.bottom + 4;
    } else {
      top = Math.max(4, rect.top - menuHeight);
    }
    const left = Math.max(4, rect.right - 208);

    addMenuPosition.value = { top: `${top}px`, left: `${left}px` };
    showAddMenu.value = true;
  }
};

const closeAddMenu = () => {
  showAddMenu.value = false;
};

// Add click outside listener
onMounted(() => {
  const handleClickOutside = (event: MouseEvent) => {
    const target = event.target as HTMLElement;

    // Handle field selector click outside
    if (showFieldSelector.value !== null) {
      const dropdown = fieldDropdownRef.value;
      const button = dropdownButtonRef.value;

      if ((!dropdown || !dropdown.contains(target)) &&
          (!button || !button.contains(target))) {
        closeFieldSelector();
      }
    }

    // Handle value_ref selector click outside
    if (showValueRefSelector.value !== null) {
      const dropdown = valueRefDropdownRef.value;
      const button = valueRefButtonRef.value;

      if ((!dropdown || !dropdown.contains(target)) &&
          (!button || !button.contains(target))) {
        closeValueRefSelector();
      }
    }

    // Handle add menu click outside
    if (showAddMenu.value) {
      const menu = document.querySelector('[data-add-menu]');
      const button = addMenuBtnRef.value;

      if ((!menu || !menu.contains(target)) &&
          (!button || !button.contains(target))) {
        closeAddMenu();
      }
    }
  };

  document.addEventListener('click', handleClickOutside);
});

// Expose hasUnsavedChanges and restoreOriginal to parent component
defineExpose({
  hasUnsavedChanges,
  restoreOriginal
});
</script>

<template>
  <div class="space-y-4">
    <!-- Loading Context Structure Warning -->
    <div v-if="depth === 0 && !policyStore.decisionalContextStructure" class="alert alert-info">
      <PhInfo :size="24" />
      <div>
        <h3 class="font-bold">Loading Decisional Context Structure</h3>
        <div class="text-sm">Field suggestions will be available once the context structure is loaded.</div>
      </div>
    </div>

    <!-- Tabs for Builder/JSON view (only show at root level) -->
    <div v-if="depth === 0" class="space-y-4">
      <div class="flex justify-between items-center">
        <h3 class="text-lg font-semibold">Conditions</h3>
        <div role="tablist" class="tabs tabs-boxed">
          <a
            role="tab"
            class="tab gap-2"
            :class="{ 'tab-active': viewMode === 'builder' }"
            @click="viewMode = 'builder'; updateJson()"
          >
            <PhTree :size="16" />
            Builder
          </a>
          <a
            role="tab"
            class="tab gap-2"
            :class="{ 'tab-active': viewMode === 'graph' }"
            @click="viewMode = 'graph'"
          >
            <PhGraph :size="16" />
            Graph
          </a>
          <a
            role="tab"
            class="tab gap-2"
            :class="{ 'tab-active': viewMode === 'json' }"
            @click="viewMode = 'json'; updateJson()"
          >
            <PhBracketsAngle :size="16" />
            JSON
          </a>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="flex justify-between items-center">
        <!-- Left: God Mode & Validate -->
        <div class="flex gap-2">
          <button
            @click="godMode = !godMode"
            type="button"
            class="btn btn-sm"
            :class="godMode ? 'btn-warning' : 'btn-outline'"
            title="Enable advanced editing mode"
          >
            <PhLock v-if="!godMode" :size="16" />
            <PhLockOpen v-else :size="16" />
            {{ godMode ? 'Advanced Mode: ON' : 'Advanced Mode: OFF' }}
          </button>

          <button
            @click="validateConditions"
            type="button"
            class="btn btn-sm btn-outline"
            :disabled="isValidating"
          >
            <PhCheck v-if="!isValidating" :size="16" />
            <span v-if="isValidating" class="loading loading-spinner loading-xs"></span>
            Validate
          </button>
        </div>

        <!-- Right: Save & Cancel -->
        <div v-if="hasChanges" class="flex gap-2">
          <button
            @click="cancelChanges"
            type="button"
            class="btn btn-sm btn-ghost"
          >
            <PhX :size="16" />
            Cancel
          </button>
          <button
            @click="saveChanges"
            type="button"
            class="btn btn-sm btn-primary"
          >
            <PhFloppyDisk :size="16" />
            Save Conditions
          </button>
        </div>
      </div>

      <!-- God Mode Warning -->
      <div v-if="godMode" class="alert alert-warning shadow-lg">
        <PhWarning :size="24" />
        <div>
          <h3 class="font-bold">Advanced Mode Enabled</h3>
          <div class="text-sm">You can now change logical operators and delete conditions. Field paths are protected and can only be selected from available options.</div>
        </div>
      </div>

      <!-- Validation Results -->
      <div v-if="validationResult" class="alert" :class="{
        'alert-success': validationResult.is_valid,
        'alert-error': !validationResult.is_valid
      }">
        <PhCheckCircle v-if="validationResult.is_valid" :size="24" weight="fill" />
        <PhXCircle v-else :size="24" weight="fill" />
        <div class="flex-1">
          <div class="font-semibold">
            {{ validationResult.is_valid ? 'Conditions are valid' : 'Validation failed' }}
          </div>
          <div v-if="!validationResult.is_valid" class="text-sm mt-2 space-y-1">
            <div v-if="validationResult.validation_errors.length > 0">
              <div class="font-medium">Validation Errors:</div>
              <ul class="list-disc list-inside">
                <li v-for="(error, idx) in validationResult.validation_errors" :key="idx">{{ error }}</li>
              </ul>
            </div>
            <div v-if="validationResult.syntax_errors.length > 0">
              <div class="font-medium">Syntax Errors:</div>
              <ul class="list-disc list-inside">
                <li v-for="(error, idx) in validationResult.syntax_errors" :key="idx">{{ error }}</li>
              </ul>
            </div>
            <div v-if="validationResult.field_errors.length > 0">
              <div class="font-medium">Field Errors:</div>
              <ul class="list-disc list-inside">
                <li v-for="(error, idx) in validationResult.field_errors" :key="idx">{{ error }}</li>
              </ul>
            </div>
          </div>
        </div>
        <span v-if="isValidating" class="loading loading-spinner loading-sm"></span>
        <button
          @click="validationResult = null"
          class="btn btn-ghost btn-sm btn-circle"
          aria-label="Close validation results"
        >
          <PhX :size="20" />
        </button>
      </div>
    </div>

    <!-- JSON View (only at root level) -->
    <div v-if="depth === 0 && viewMode === 'json'">
      <div v-if="!godMode" class="alert alert-info mb-4">
        <PhInfo :size="24" />
        <span>JSON editing is disabled in basic mode. Enable Advanced Mode to edit directly.</span>
      </div>
      <JsonEditor
        v-model="jsonString"
        :readonly="!godMode"
      />
      <button
        v-if="godMode"
        @click="updateFromJson"
        class="btn btn-sm btn-primary mt-2"
      >
        Apply JSON Changes
      </button>
    </div>

    <!-- Graph View (only at root level) -->
    <div v-if="depth === 0 && viewMode === 'graph'" class="h-[600px] border border-base-300 rounded-lg overflow-hidden">
      <RuleConditionGraph
        :conditions="workingValue"
        :available-fields="availableFields"
      />
    </div>

    <!-- Builder View -->
    <div v-if="depth > 0 || viewMode === 'builder'">
      <!-- Empty object - show initialization button -->
      <div v-if="isEmpty(workingValue)" class="text-center py-8">
        <p class="text-sm text-base-content/50 mb-4">No conditions defined</p>
        <div class="flex gap-2 justify-center">
          <button
            @click="updateWorkingValue(defaultAllOfRule)"
            class="btn btn-sm btn-primary"
            type="button"
          >
            Start with ALL OF (AND)
          </button>
          <button
            @click="updateWorkingValue(defaultAnyOfRule)"
            class="btn btn-sm btn-secondary"
            type="button"
          >
            Start with ANY OF (OR)
          </button>
          <button
            @click="updateWorkingValue(defaultNotRule)"
            class="btn btn-sm btn-accent"
            type="button"
          >
            Start with NOT
          </button>
        </div>
      </div>

      <!-- Condition (leaf node) -->
      <div v-else-if="isCondition(workingValue)" class="space-y-2">
        <div class="flex gap-2 items-start">
          <!-- Field Selector -->
          <div class="flex-1 relative">
            <!-- Dropdown Selector (only in advanced mode) -->
            <div v-if="isGodModeEnabled" class="relative w-full">
              <button
                ref="dropdownButtonRef"
                type="button"
                @click="toggleFieldSelector(0)"
                class="btn btn-sm w-full justify-between font-mono text-xs"
                :class="(isCondition(workingValue) && workingValue.field) ? 'btn-outline' : 'btn-ghost border-dashed'"
              >
                <span class="truncate" :class="!(isCondition(workingValue) && workingValue.field) && 'text-base-content/50'">
                  {{ (isCondition(workingValue) && workingValue.field) || 'Select field...' }}
                </span>
                <PhCaretDown :size="16" class="flex-shrink-0" />
              </button>

              <!-- Dropdown Menu -->
              <Teleport to="body">
                <div
                  ref="fieldDropdownRef"
                  v-if="showFieldSelector === 0"
                  class="fixed z-[9999] w-[700px] max-w-[95vw] shadow-2xl bg-base-100 border border-base-300 rounded-lg"
                  :style="{ top: 'var(--dropdown-top, 0px)', left: 'var(--dropdown-left, 0px)' }"
                  @click.stop
                  @keydown.esc="closeFieldSelector"
                >
                <div class="p-2">
                  <!-- Header with close button -->
                  <div class="flex items-center justify-between mb-2">
                    <h4 class="text-sm font-semibold text-base-content/70">Select Field</h4>
                    <button
                      type="button"
                      @click="closeFieldSelector"
                      class="btn btn-ghost btn-xs btn-circle"
                      aria-label="Close field selector"
                    >
                      <PhX :size="16" />
                    </button>
                  </div>

                  <!-- Search Box -->
                  <div class="relative">
                    <PhListMagnifyingGlass :size="16" class="absolute left-3 top-1/2 -translate-y-1/2 text-base-content/50 pointer-events-none z-10" />
                    <input
                      v-model="fieldSearchQuery"
                      type="text"
                      placeholder="Search fields..."
                      class="input input-bordered input-sm w-full pl-9"
                      @click.stop
                      @keydown.esc="closeFieldSelector"
                    />
                  </div>

                  <!-- Field List -->
                  <div class="max-h-[500px] overflow-y-auto space-y-1 mt-2">
                    <div v-if="Object.keys(groupedFields).length === 0" class="text-center py-4 text-base-content/50">
                      No fields found
                    </div>
                    <div v-else>
                      <div v-for="(groupFields, group) in groupedFields" :key="group" class="mb-3">
                        <!-- Find the parent field to get its description -->
                        <div class="text-xs font-semibold text-base-content/70 px-2 py-1 bg-base-200 rounded mb-1 sticky top-0 z-10 flex items-center justify-between gap-2">
                          <span>{{ group }}</span>
                          <span class="text-xs font-normal text-base-content/50">
                            {{ availableFields.find(f => f.path === group)?.description || '' }}
                          </span>
                        </div>
                        <button
                          v-for="field in groupFields.filter(f => !f.children || f.children.length === 0)"
                          :key="field.path"
                          type="button"
                          @click.stop="handleFieldSelect(field.path)"
                          class="w-full text-left px-3 py-2 rounded transition-colors hover:bg-base-200 cursor-pointer"
                          :class="{ 'bg-primary/10': isCondition(workingValue) && workingValue.field === field.path }"
                        >
                          <div class="flex items-start justify-between gap-3">
                            <div class="flex-1 min-w-0">
                              <div class="font-mono text-sm font-medium" :class="field.is_optional && 'text-base-content/70'">
                                {{ field.path }}
                                <span v-if="field.is_optional" class="text-xs text-warning ml-1">optional</span>
                              </div>
                              <div class="text-xs text-base-content/60 mt-0.5">
                                {{ field.description }}
                              </div>
                            </div>
                            <div class="badge badge-sm badge-ghost flex-shrink-0">
                              {{ field.type }}
                            </div>
                          </div>
                          <!-- Show predefined values if available -->
                          <div v-if="field.values && field.values.length > 0" class="mt-1.5 flex flex-wrap gap-1">
                            <span
                              v-for="val in field.values.slice(0, 8)"
                              :key="val"
                              class="badge badge-xs badge-outline"
                            >
                              {{ val }}
                            </span>
                            <span v-if="field.values.length > 8" class="badge badge-xs badge-ghost">
                              +{{ field.values.length - 8 }}
                            </span>
                          </div>
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
                </div>
              </Teleport>
            </div>

            <!-- Read-only field display (in basic mode) -->
            <div v-else class="relative w-full">
              <input
                :value="isCondition(workingValue) && workingValue.field ? workingValue.field : 'No field selected'"
                type="text"
                :placeholder="isCondition(workingValue) && workingValue.field ? workingValue.field : 'No field selected'"
                class="input input-bordered input-sm w-full font-mono text-xs"
                readonly
              />
            </div>

            <!-- Field Description (below dropdown/display) -->
            <div v-if="isCondition(workingValue) && workingValue.field && getFieldInfo(workingValue.field)" class="px-1 mt-1">
              <div class="text-xs text-base-content/60">
                {{ getFieldInfo(workingValue.field)?.description }}
              </div>
            </div>

            <datalist id="field-suggestions">
              <option v-for="field in fieldSuggestions" :key="field" :value="field" />
            </datalist>
          </div>

          <!-- Operator Selector -->
          <select
            :value="workingValue.operator"
            @change="handleOperatorChange"
            class="select select-bordered select-sm w-50"
          >
            <option v-for="op in operators" :key="op.value" :value="op.value">
              {{ op.label }}
            </option>
          </select>

          <!-- Value Input with Type Info -->
          <div class="flex flex-col">
            <!-- Mode Toggle (Static / Field Ref) -->
            <div v-if="isGodModeEnabled" class="flex items-center gap-1 mb-1">
              <button
                type="button"
                class="btn btn-xs"
                :class="!isValueRefMode ? 'btn-primary' : 'btn-ghost'"
                @click="isValueRefMode && toggleValueMode()"
                title="Compare against a static value"
              >
                Value
              </button>
              <button
                type="button"
                class="btn btn-xs"
                :class="isValueRefMode ? 'btn-primary' : 'btn-ghost'"
                @click="!isValueRefMode && toggleValueMode()"
                title="Compare against another context field"
              >
                Field Ref
              </button>
            </div>

            <!-- Static Value Input -->
            <div v-if="!isValueRefMode" class="relative">
              <!-- If field has predefined values, show dropdown -->
              <select
                v-if="getFieldInfo(workingValue.field)?.values && getFieldInfo(workingValue.field)!.values!.length > 0 && (workingValue.operator === 'eq' || workingValue.operator === 'ne')"
                :value="workingValue.value"
                @change="(e) => updateConditionField('value', (e.target as HTMLSelectElement).value)"
                class="select select-bordered select-sm w-48"
              >
                <option value="">Select value...</option>
                <option v-for="val in getFieldInfo(workingValue.field)?.values" :key="val" :value="val">
                  {{ val }}
                </option>
              </select>
              <!-- Boolean type: show toggle/select -->
              <select
                v-else-if="getFieldInfo(workingValue.field)?.type === 'bool'"
                :value="workingValue.value"
                @change="(e) => updateConditionField('value', (e.target as HTMLSelectElement).value === 'true')"
                class="select select-bordered select-sm w-48"
              >
                <option value="">Select...</option>
                <option value="true">True</option>
                <option value="false">False</option>
              </select>
              <!-- Number types: show number input -->
              <input
                v-else-if="getFieldInfo(workingValue.field)?.type === 'int' || getFieldInfo(workingValue.field)?.type === 'float'"
                :value="workingValue.value"
                @input="handleValueInput"
                type="number"
                :step="getFieldInfo(workingValue.field)?.type === 'float' ? 'any' : '1'"
                placeholder="Enter number"
                class="input input-bordered input-sm w-48"
              />
              <!-- Datetime type: show datetime-local input -->
              <input
                v-else-if="getFieldInfo(workingValue.field)?.type === 'datetime'"
                :value="workingValue.value"
                @input="handleValueInput"
                type="datetime-local"
                class="input input-bordered input-sm w-48"
              />
              <!-- Array operators: show text input for array -->
              <input
                v-else-if="workingValue.operator === 'in' || workingValue.operator === 'not_in'"
                :value="Array.isArray(workingValue.value) ? JSON.stringify(workingValue.value) : workingValue.value"
                @input="handleValueInput"
                type="text"
                placeholder="[1,2,3] or 1,2,3"
                class="input input-bordered input-sm w-48"
              />
              <!-- Default: text input for strings and other types -->
              <input
                v-else
                :value="Array.isArray(workingValue.value) ? JSON.stringify(workingValue.value) : workingValue.value"
                @input="handleValueInput"
                type="text"
                placeholder="Enter value"
                class="input input-bordered input-sm w-48"
              />
            </div>

            <!-- Field Reference Input -->
            <div v-else class="relative">
              <div v-if="isGodModeEnabled" class="relative w-48">
                <button
                  ref="valueRefButtonRef"
                  type="button"
                  @click="toggleValueRefSelector()"
                  class="btn btn-sm w-full justify-between font-mono text-xs"
                  :class="workingValue.value_ref ? 'btn-outline border-secondary' : 'btn-ghost border-dashed'"
                >
                  <span class="truncate" :class="!workingValue.value_ref && 'text-base-content/50'">
                    {{ workingValue.value_ref || 'Select field...' }}
                  </span>
                  <PhCaretDown :size="16" class="flex-shrink-0" />
                </button>

                <!-- value_ref Dropdown -->
                <Teleport to="body">
                  <div
                    ref="valueRefDropdownRef"
                    v-if="showValueRefSelector === 0"
                    class="fixed z-[9999] w-[600px] max-w-[90vw] shadow-2xl bg-base-100 border border-base-300 rounded-lg"
                    :style="{ top: 'var(--vref-dropdown-top, 0px)', left: 'var(--vref-dropdown-left, 0px)' }"
                    @click.stop
                    @keydown.esc="closeValueRefSelector"
                  >
                    <div class="p-2">
                      <div class="flex items-center justify-between mb-2">
                        <h4 class="text-sm font-semibold text-base-content/70">Select Reference Field</h4>
                        <button type="button" @click="closeValueRefSelector" class="btn btn-ghost btn-xs btn-circle">
                          <PhX :size="16" />
                        </button>
                      </div>
                      <input
                        v-model="valueRefSearchQuery"
                        type="text"
                        placeholder="Search fields..."
                        class="input input-bordered input-sm w-full mb-2"
                        @click.stop
                        @keydown.esc="closeValueRefSelector"
                      />
                      <div class="max-h-[350px] overflow-y-auto space-y-1">
                        <div v-for="(groupFields, group) in groupedValueRefFields" :key="group" class="mb-2">
                          <div class="text-xs font-semibold text-base-content/70 px-2 py-1 bg-base-200 rounded mb-1 sticky top-0 z-10">
                            {{ group }}
                          </div>
                          <button
                            v-for="field in groupFields"
                            :key="field.path"
                            type="button"
                            @click.stop="handleValueRefFieldSelect(field.path)"
                            class="w-full text-left px-3 py-1.5 rounded transition-colors hover:bg-base-200 cursor-pointer"
                            :class="{ 'bg-secondary/10': isCondition(workingValue) && workingValue.value_ref === field.path }"
                          >
                            <div class="flex items-center justify-between gap-2">
                              <span class="font-mono text-xs">{{ field.path }}</span>
                              <span class="badge badge-xs badge-ghost">{{ field.type }}</span>
                            </div>
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </Teleport>
              </div>
              <!-- Read-only in basic mode -->
              <input
                v-else
                :value="workingValue.value_ref || ''"
                type="text"
                class="input input-bordered input-sm w-48 font-mono text-xs"
                readonly
              />
            </div>

            <!-- Type Badge (below value input) -->
            <div v-if="isCondition(workingValue) && workingValue.field && getFieldInfo(workingValue.field)" class="px-1">
              <span class="text-xs text-base-content/60">{{ getFieldInfo(workingValue.field)?.type }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Group (parent node) -->
      <div v-else-if="isGroup(workingValue)" class="card bg-base-200 shadow-sm pt-4" :class="`ml-${depth * 4}`">
        <div class="card-body p-4 gap-3">
          <!-- Group header -->
          <div class="flex items-center justify-between gap-2">
            <div class="flex items-center gap-2">
              <button
                @click.prevent.stop="isGodModeEnabled && toggleGroupType($event)"
                type="button"
                class="btn btn-sm"
                :class="{
                  'btn-primary': groupType === 'all_of',
                  'btn-secondary': groupType === 'any_of',
                  'btn-accent': groupType === 'not_',
                  'pointer-events-none': !isGodModeEnabled
                }"
                :disabled="!isGodModeEnabled"
                :title="isGodModeEnabled ? 'Click to change logical operator' : 'Enable Advanced Mode to change logical operator'"
              >
                {{ groupType === 'all_of' ? 'ALL OF' : groupType === 'any_of' ? 'ANY OF' : 'NOT' }}
              </button>
              <span class="text-sm opacity-70">
                {{ groupType === 'all_of' ? '(AND logic)' : groupType === 'any_of' ? '(OR logic)' : '(NOT logic)' }}
              </span>
            </div>

            <div v-if="isGodModeEnabled" class="flex gap-1">
              <button
                ref="addMenuBtnRef"
                type="button"
                @click.stop="toggleAddMenu"
                class="btn btn-sm btn-ghost"
              >
                <PhPlus :size="16" />
                Add
              </button>
              <Teleport to="body">
                <ul
                  v-if="showAddMenu"
                  data-add-menu
                  class="fixed z-[9999] menu p-2 shadow-lg bg-base-100 border border-base-300 rounded-box w-52"
                  :style="addMenuPosition"
                  @click.stop
                >
                  <li><a @click="addCondition(); closeAddMenu()">Add Condition</a></li>
                  <li><a @click="addGroup('all_of'); closeAddMenu()">Add ALL OF Group</a></li>
                  <li><a @click="addGroup('any_of'); closeAddMenu()">Add ANY OF Group</a></li>
                  <li><a @click="addGroup('not_'); closeAddMenu()">Add NOT Group</a></li>
                </ul>
              </Teleport>
            </div>
          </div>

          <!-- Group items -->
          <div class="space-y-2">
            <div
              v-for="(item, index) in groupItems"
              :key="index"
              class="flex gap-2 items-start"
            >
              <div class="flex-1">
                <RuleConditionBuilder
                  :model-value="item"
                  @update:model-value="updateGroupItem(index, $event)"
                  :depth="depth + 1"
                  :god-mode="isGodModeEnabled"
                />
              </div>

              <button
                v-if="isGodModeEnabled"
                @click="removeItem(index)"
                class="btn btn-sm btn-ghost btn-circle text-error"
                :disabled="groupItems.length === 1 || groupType === 'not_'"
                :title="groupItems.length === 1 ? 'Cannot remove the last item' : groupType === 'not_' ? 'NOT group must have exactly one item' : 'Remove this condition'"
              >
                <PhX :size="16" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Custom depth-based margin for nested groups */
.ml-0 { margin-left: 0; }
.ml-4 { margin-left: 1rem; }
.ml-8 { margin-left: 2rem; }
.ml-12 { margin-left: 3rem; }
.ml-16 { margin-left: 4rem; }
</style>

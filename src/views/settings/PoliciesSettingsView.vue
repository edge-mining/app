<script setup lang="ts">
import { onMounted, ref, computed } from "vue";
import { usePolicyStore } from "../../core/stores/policyStore";
import PolicyRow from "../../components/policies/PolicyRow.vue";
import PolicyRuleRow from "../../components/policies/PolicyRuleRow.vue";
import RuleConditionBuilder from "../../components/policies/RuleConditionBuilder.vue";
import type {
  OptimizationPolicy,
  AutomationRule,
  PolicyCheckResult,
  RuleType,
} from "../../core/models/policy";
import {
  PhPlay,
  PhStop,
  PhWarning,
  PhArrowCounterClockwise,
  PhCopy,
  PhMagnifyingGlass,
  PhX,
} from "@phosphor-icons/vue";

const policyStore = usePolicyStore();

// Policy modal state
const newPolicy = ref<OptimizationPolicy | undefined>(undefined);
const editingPolicy = ref<OptimizationPolicy | undefined>(undefined);
const showPolicyModal = ref(false);
const isEditingPolicy = ref(false);

// Rule modal state
const selectedPolicy = ref<OptimizationPolicy | undefined>(undefined);
const newRule = ref<AutomationRule | undefined>(undefined);
const editingRule = ref<AutomationRule | undefined>(undefined);
const showRulesModal = ref(false);
const showRuleEditModal = ref(false);
const isEditingRule = ref(false);
const activeRuleTab = ref<RuleType>("start");
const currentRuleType = ref<RuleType>("start");

// Copy From modal state
const showCopyFromModal = ref(false);
const copyTargetRule = ref<"new" | "editing">("new");
const copyOnlyConditions = ref(false);
const copyFromSearchQuery = ref("");

// Check result modal state
const showCheckModal = ref(false);
const checkResult = ref<PolicyCheckResult | null>(null);
const checkingPolicyName = ref("");

// Rule error state
const ruleDeleteError = ref("");
const ruleAddSaveError = ref("");

// Reference to RuleConditionBuilder components
const editingRuleConditionBuilder = ref<InstanceType<
  typeof RuleConditionBuilder
> | null>(null);
const newRuleConditionBuilder = ref<InstanceType<
  typeof RuleConditionBuilder
> | null>(null);

// Track original conditions for rules (to detect unsaved changes)
const originalEditingRuleConditions = ref<any>(null);
const originalNewRuleConditions = ref<any>(null);

// Computed to check if conditions changed from original
const editingRuleHasUnsavedConditions = computed(() => {
  if (!editingRule.value || !originalEditingRuleConditions.value) return false;
  return (
    JSON.stringify(editingRule.value.conditions) !==
    JSON.stringify(originalEditingRuleConditions.value)
  );
});

const newRuleHasUnsavedConditions = computed(() => {
  if (!newRule.value || !originalNewRuleConditions.value) return false;
  return (
    JSON.stringify(newRule.value.conditions) !==
    JSON.stringify(originalNewRuleConditions.value)
  );
});

onMounted(() => {
  policyStore.loadPolicies();
});

// Policy CRUD handlers
function addPolicy() {
  newPolicy.value = {
    id: "",
    name: "",
    description: "",
    start_rules: [],
    stop_rules: [],
    metadata: {
      author: undefined,
      version: undefined,
      created: undefined,
      last_modified: undefined,
    },
  };
  isEditingPolicy.value = false;
  showPolicyModal.value = true;
}

function handleEditPolicy(policy: OptimizationPolicy) {
  editingPolicy.value = {
    ...policy,
    metadata: policy.metadata || {
      author: undefined,
      version: undefined,
      created: undefined,
      last_modified: undefined,
    },
  };
  isEditingPolicy.value = true;
  showPolicyModal.value = true;
}

function cancelPolicyModal() {
  newPolicy.value = undefined;
  editingPolicy.value = undefined;
  isEditingPolicy.value = false;
  showPolicyModal.value = false;
}

function confirmAddPolicy() {
  if (!newPolicy.value) return;
  policyStore.addPolicy(newPolicy.value).then(() => {
    policyStore.loadPolicies();
    newPolicy.value = undefined;
    showPolicyModal.value = false;
  });
}

function confirmEditPolicy() {
  if (!editingPolicy.value) return;
  policyStore
    .updatePolicy(editingPolicy.value.id!.toString(), editingPolicy.value)
    .then(() => {
      policyStore.loadPolicies();
      editingPolicy.value = undefined;
      isEditingPolicy.value = false;
      showPolicyModal.value = false;
    });
}

function handleDeletePolicy(policy: OptimizationPolicy) {
  policyStore.deletePolicy(policy.id!.toString()).then(() => {
    policyStore.loadPolicies();
  });
}

function handleCheckPolicy(policy: OptimizationPolicy) {
  checkingPolicyName.value = policy.name;
  policyStore.checkPolicy(policy.id!.toString()).then((result) => {
    checkResult.value = result;
    showCheckModal.value = true;
  });
}

function closeCheckModal() {
  showCheckModal.value = false;
  checkResult.value = null;
}

// Rule management handlers
function handleManageRules(policy: OptimizationPolicy) {
  selectedPolicy.value = policy;
  ruleDeleteError.value = "";
  ruleAddSaveError.value = "";
  showRulesModal.value = true;
}

function closeRulesModal() {
  showRulesModal.value = false;
  selectedPolicy.value = undefined;
  ruleDeleteError.value = "";
  ruleAddSaveError.value = "";
}

function addRule() {
  currentRuleType.value = activeRuleTab.value;
  ruleAddSaveError.value = "";
  newRule.value = {
    id: "",
    name: "",
    description: "",
    priority: 10,
    enabled: true,
    conditions: {},
  };
  originalNewRuleConditions.value = JSON.parse(
    JSON.stringify(newRule.value.conditions),
  );
  isEditingRule.value = false;
  showRuleEditModal.value = true;
}

function handleEditRule(rule: AutomationRule, ruleType: RuleType) {
  currentRuleType.value = ruleType;
  ruleAddSaveError.value = "";
  editingRule.value = { ...rule };
  originalEditingRuleConditions.value = JSON.parse(
    JSON.stringify(rule.conditions),
  );
  isEditingRule.value = true;
  showRuleEditModal.value = true;
}

function cancelRuleModal() {
  newRule.value = undefined;
  editingRule.value = undefined;
  originalNewRuleConditions.value = null;
  originalEditingRuleConditions.value = null;
  isEditingRule.value = false;
  ruleDeleteError.value = "";
  ruleAddSaveError.value = "";
  showRuleEditModal.value = false;
}

function confirmAddRule() {
  if (!newRule.value || !selectedPolicy.value) return;
  ruleDeleteError.value = "";
  policyStore
    .addRule(
      selectedPolicy.value.id!.toString(),
      currentRuleType.value,
      newRule.value,
    )
    .then(() => {
      // Reload the policy to get updated rules
      policyStore
        .loadPolicy(selectedPolicy.value!.id!.toString())
        .then((updatedPolicy) => {
          selectedPolicy.value = updatedPolicy;
        });
      policyStore.loadPolicies();
      newRule.value = undefined;
      originalNewRuleConditions.value = null;
      showRuleEditModal.value = false;
    })
    .catch((error) => {
      let errorMsg = "Unknown error";
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail;
        errorMsg = Array.isArray(detail) ? detail[0]?.msg : detail;
      } else if (error.message) {
        errorMsg = error.message;
      }
      ruleAddSaveError.value = errorMsg;
    });
}

function confirmEditRule() {
  if (!editingRule.value || !selectedPolicy.value) return;
  ruleAddSaveError.value = "";
  policyStore
    .updateRule(
      selectedPolicy.value.id!.toString(),
      editingRule.value.id!.toString(),
      editingRule.value,
    )
    .then(() => {
      policyStore
        .loadPolicy(selectedPolicy.value!.id!.toString())
        .then((updatedPolicy) => {
          selectedPolicy.value = updatedPolicy;
        });
      policyStore.loadPolicies();
      editingRule.value = undefined;
      originalEditingRuleConditions.value = null;
      isEditingRule.value = false;
      showRuleEditModal.value = false;
    })
    .catch((error) => {
      let errorMsg = "Unknown error";
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail;
        errorMsg = Array.isArray(detail) ? detail[0]?.msg : detail;
      } else if (error.message) {
        errorMsg = error.message;
      }
      ruleAddSaveError.value = errorMsg;
    });
}

function handleDeleteRule(rule: AutomationRule) {
  if (!selectedPolicy.value) return;
  policyStore
    .deleteRule(selectedPolicy.value.id!.toString(), rule.id!.toString())
    .then(() => {
      policyStore
        .loadPolicy(selectedPolicy.value!.id!.toString())
        .then((updatedPolicy) => {
          selectedPolicy.value = updatedPolicy;
        });
      policyStore.loadPolicies();
    })
    .catch((error) => {
      let errorMsg = "Unknown error";
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail;
        errorMsg = Array.isArray(detail) ? detail[0]?.msg : detail;
      } else if (error.message) {
        errorMsg = error.message;
      }
      ruleDeleteError.value = errorMsg;
    });
}

// Restore original conditions for editing rule
function restoreEditingRuleConditions() {
  if (editingRule.value && originalEditingRuleConditions.value) {
    editingRule.value.conditions = JSON.parse(
      JSON.stringify(originalEditingRuleConditions.value),
    );
  }
}

// Restore original conditions for new rule
function restoreNewRuleConditions() {
  if (newRule.value && originalNewRuleConditions.value) {
    newRule.value.conditions = JSON.parse(
      JSON.stringify(originalNewRuleConditions.value),
    );
  }
}

function handleToggleRuleEnabled(rule: AutomationRule) {
  if (!selectedPolicy.value) return;
  const policyId = selectedPolicy.value.id!.toString();
  const ruleId = rule.id!.toString();

  const action = rule.enabled
    ? policyStore.disableRule(policyId, ruleId)
    : policyStore.enableRule(policyId, ruleId);

  action.then(() => {
    policyStore.loadPolicy(policyId).then((updatedPolicy) => {
      selectedPolicy.value = updatedPolicy;
    });
    policyStore.loadPolicies();
  });
}

// Copy From functionality
function openCopyFromModal(target: "new" | "editing") {
  copyTargetRule.value = target;
  copyOnlyConditions.value = false;
  showCopyFromModal.value = true;
}

function closeCopyFromModal() {
  showCopyFromModal.value = false;
  copyOnlyConditions.value = false;
  copyFromSearchQuery.value = "";
}

function copyFromRule(
  _sourcePolicy: OptimizationPolicy,
  sourceRule: AutomationRule,
  _ruleType: RuleType,
) {
  const targetRule =
    copyTargetRule.value === "new" ? newRule.value : editingRule.value;

  if (!targetRule) return;

  if (copyOnlyConditions.value) {
    // Copy only conditions
    targetRule.conditions = JSON.parse(JSON.stringify(sourceRule.conditions));
  } else {
    // Copy all fields except id (keep the target's id or empty for new)
    const targetId = targetRule.id;
    Object.assign(targetRule, {
      ...sourceRule,
      id: targetId,
      // Deep clone conditions to avoid reference issues
      conditions: JSON.parse(JSON.stringify(sourceRule.conditions)),
    });
  }

  // Update original conditions tracking
  if (copyTargetRule.value === "new") {
    originalNewRuleConditions.value = JSON.parse(
      JSON.stringify(targetRule.conditions),
    );
  } else {
    originalEditingRuleConditions.value = JSON.parse(
      JSON.stringify(targetRule.conditions),
    );
  }

  closeCopyFromModal();
}

// Get all available rules from all policies for copy from modal
const allAvailableRules = computed(() => {
  const rules: Array<{
    policy: OptimizationPolicy;
    rule: AutomationRule;
    type: RuleType;
  }> = [];

  policyStore.policies.forEach((policy) => {
    policy.start_rules?.forEach((rule) => {
      rules.push({ policy, rule, type: "start" });
    });
    policy.stop_rules?.forEach((rule) => {
      rules.push({ policy, rule, type: "stop" });
    });
  });

  return rules;
});

// Filter rules based on search query
const filteredAvailableRules = computed(() => {
  if (!copyFromSearchQuery.value) return allAvailableRules.value;

  const query = copyFromSearchQuery.value.toLowerCase();
  return allAvailableRules.value.filter(({ policy, rule, type }) => {
    return (
      policy.name.toLowerCase().includes(query) ||
      (policy.description?.toLowerCase() || "").includes(query) ||
      rule.name.toLowerCase().includes(query) ||
      (rule.description?.toLowerCase() || "").includes(query) ||
      type.toLowerCase().includes(query)
    );
  });
});
</script>

<template>
  <h1 class="text-3xl font-bold">Optimization Policy Settings</h1>

  <div class="overflow-x-auto">
    <table class="table">
      <thead>
        <tr>
          <th>Name / Description</th>
          <th>Author</th>
          <th>Modified</th>
          <th>Start Rules</th>
          <th>Stop Rules</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <PolicyRow
          v-for="(policy, i) in policyStore.policies"
          :key="policy.id"
          v-model="policyStore.policies[i]"
          @edit="handleEditPolicy"
          @delete="handleDeletePolicy"
          @manage-rules="handleManageRules"
          @check="handleCheckPolicy"
        />

        <tr>
          <th colspan="6" class="text-center">
            <button class="btn btn-primary" @click="addPolicy">
              Add Policy
            </button>
          </th>
        </tr>
      </tbody>
    </table>
  </div>

  <!-- Policy Add/Edit Modal -->
  <dialog :class="['modal', { 'modal-open': showPolicyModal }]">
    <div v-if="newPolicy || editingPolicy" class="modal-box max-w-2xl">
      <h3 class="font-bold text-lg mb-4">
        {{ isEditingPolicy ? "Edit Policy" : "Add Policy" }}
      </h3>

      <form
        @submit.prevent="
          isEditingPolicy ? confirmEditPolicy() : confirmAddPolicy()
        "
        class="flex flex-col gap-4"
      >
        <template v-if="isEditingPolicy && editingPolicy">
          <!-- Name field -->
          <div class="space-y-1">
            <div class="font-medium">
              Name
              <span class="text-sm text-error opacity-60 ml-1 font-normal"
                >(required)</span
              >
            </div>
            <input
              v-model="editingPolicy.name"
              type="text"
              placeholder="Policy name"
              required
              class="input input-bordered input-sm w-full"
            />
          </div>

          <div class="space-y-1">
            <div class="font-medium">Description</div>
            <textarea
              v-model="editingPolicy.description"
              placeholder="Policy description"
              class="textarea textarea-bordered textarea-sm w-full"
              rows="3"
            ></textarea>
          </div>

          <!-- Metadata Section -->
          <div class="divider text-sm">Metadata</div>

          <div class="grid grid-cols-4 gap-4">
            <div class="space-y-1">
              <div class="font-medium">Author</div>
              <div class="text-sm opacity-70">
                {{ editingPolicy.metadata?.author || "—" }}
              </div>
            </div>

            <div class="space-y-1">
              <div class="font-medium">Version</div>
              <div class="text-sm opacity-70">
                {{ editingPolicy.metadata?.version || "—" }}
              </div>
            </div>

            <div class="space-y-1">
              <div class="font-medium">Created</div>
              <div class="text-sm opacity-70">
                {{ editingPolicy.metadata?.created || "—" }}
              </div>
            </div>

            <div class="space-y-1">
              <div class="font-medium">Last Modified</div>
              <div class="text-sm opacity-70">
                {{ editingPolicy.metadata?.last_modified || "—" }}
              </div>
            </div>
          </div>
        </template>

        <template v-else-if="newPolicy">
          <div class="space-y-1">
            <div class="font-medium">
              Name
              <span class="text-sm text-error opacity-60 ml-1 font-normal"
                >(required)</span
              >
            </div>
            <input
              v-model="newPolicy.name"
              type="text"
              placeholder="Policy name"
              required
              class="input input-bordered input-sm w-full"
            />
          </div>

          <div class="space-y-1">
            <div class="font-medium">Description</div>
            <textarea
              v-model="newPolicy.description"
              placeholder="Policy description"
              class="textarea textarea-bordered textarea-sm w-full"
              rows="3"
            ></textarea>
          </div>
        </template>

        <div class="modal-action">
          <button
            type="button"
            class="btn btn-secondary"
            @click="cancelPolicyModal"
          >
            Cancel
          </button>
          <button type="submit" class="btn btn-primary">
            {{ isEditingPolicy ? "Save" : "Add" }}
          </button>
        </div>
      </form>
    </div>
    <form method="dialog" class="modal-backdrop">
      <button @click="cancelPolicyModal">close</button>
    </form>
  </dialog>

  <!-- Rules Management Modal -->
  <dialog :class="['modal', { 'modal-open': showRulesModal }]">
    <div v-if="selectedPolicy" class="modal-box max-w-4xl">
      <h3 class="font-bold text-lg mb-4">
        Rules for "{{ selectedPolicy.name }}"
      </h3>

      <!-- Tabs for Start/Stop Rules -->
      <div class="tabs tabs-lifted justify-center">
        <label class="tab">
          <input
            type="radio"
            name="rule_tabs"
            :checked="activeRuleTab === 'start'"
            @change="activeRuleTab = 'start'"
          />
          <PhPlay :size="16" class="me-2" />
          Start Rules
        </label>
        <div class="tab-content bg-base-100 border-base-300 p-6">
          <div class="overflow-x-auto">
            <table class="table table-sm">
              <thead>
                <tr>
                  <th>Enabled</th>
                  <th>Name / Description</th>
                  <th>Priority</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <template
                  v-if="
                    selectedPolicy.start_rules &&
                    selectedPolicy.start_rules.length > 0
                  "
                >
                  <PolicyRuleRow
                    v-for="(rule, i) in selectedPolicy.start_rules"
                    :key="rule.id"
                    v-model="selectedPolicy.start_rules[i]"
                    @edit="(r) => handleEditRule(r, 'start')"
                    @delete="(r) => handleDeleteRule(r)"
                    @toggle-enabled="(r) => handleToggleRuleEnabled(r)"
                  />
                </template>
                <tr v-else>
                  <td colspan="4" class="text-center text-base-content/50">
                    No start rules defined for this policy
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <label class="tab">
          <input
            type="radio"
            name="rule_tabs"
            :checked="activeRuleTab === 'stop'"
            @change="activeRuleTab = 'stop'"
          />
          <PhStop :size="16" class="me-2" />
          Stop Rules
        </label>
        <div class="tab-content bg-base-100 border-base-300 p-6">
          <div class="overflow-x-auto">
            <table class="table table-sm">
              <thead>
                <tr>
                  <th>Enabled</th>
                  <th>Name / Description</th>
                  <th>Priority</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <template
                  v-if="
                    selectedPolicy.stop_rules &&
                    selectedPolicy.stop_rules.length > 0
                  "
                >
                  <PolicyRuleRow
                    v-for="(rule, i) in selectedPolicy.stop_rules"
                    :key="rule.id"
                    v-model="selectedPolicy.stop_rules[i]"
                    @edit="(r) => handleEditRule(r, 'stop')"
                    @delete="(r) => handleDeleteRule(r)"
                    @toggle-enabled="(r) => handleToggleRuleEnabled(r)"
                  />
                </template>
                <tr v-else>
                  <td colspan="4" class="text-center text-base-content/50">
                    No stop rules defined for this policy
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div class="modal-action">
        <div v-if="ruleDeleteError" class="flex-1 mr-auto">
          <div class="text-error text-sm">
            <span class="font-semibold">Error:</span> {{ ruleDeleteError }}
          </div>
        </div>
        <button class="btn btn-primary" @click="addRule">
          Add {{ activeRuleTab === "start" ? "Start" : "Stop" }} Rule
        </button>
        <button class="btn btn-secondary" @click="closeRulesModal">
          Close
        </button>
      </div>
    </div>
    <form method="dialog" class="modal-backdrop">
      <button @click="closeRulesModal">close</button>
    </form>
  </dialog>

  <!-- Rule Add/Edit Modal -->
  <dialog :class="['modal', { 'modal-open': showRuleEditModal }]">
    <div v-if="newRule || editingRule" class="modal-box max-w-5xl">
      <div class="flex justify-between items-center mb-4">
        <h3 class="font-bold text-lg">
          {{ isEditingRule ? "Edit" : "Add" }}
          {{ currentRuleType === "start" ? "Start" : "Stop" }} Rule
        </h3>
        <button
          type="button"
          class="btn btn-sm btn-outline"
          @click="openCopyFromModal(isEditingRule ? 'editing' : 'new')"
          title="Copy from another rule"
        >
          <PhCopy :size="16" />
          Copy From
        </button>
      </div>

      <form
        @submit.prevent="isEditingRule ? confirmEditRule() : confirmAddRule()"
        class="flex flex-col gap-4"
      >
        <template v-if="isEditingRule && editingRule">
          <div class="space-y-1">
            <div class="font-medium">
              Name
              <span class="text-sm text-error opacity-60 ml-1 font-normal"
                >(required)</span
              >
            </div>
            <input
              v-model="editingRule.name"
              type="text"
              placeholder="Rule name"
              required
              class="input input-bordered input-sm w-full"
            />
          </div>

          <div class="space-y-1">
            <div class="font-medium">Description</div>
            <textarea
              v-model="editingRule.description"
              placeholder="Rule description"
              class="textarea textarea-bordered textarea-sm w-full"
              rows="2"
            ></textarea>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div class="space-y-1">
              <div class="font-medium">Priority</div>
              <input
                v-model.number="editingRule.priority"
                type="number"
                placeholder="Priority (higher = higher priority)"
                class="input input-bordered input-sm w-full"
              />
              <div class="text-sm italic opacity-70">
                Higher values have higher priority
              </div>
            </div>

            <div class="space-y-1 flex items-center">
              <label class="label cursor-pointer justify-start gap-4 p-0">
                <input
                  v-model="editingRule.enabled"
                  type="checkbox"
                  class="toggle toggle-primary toggle-sm"
                />
                <span class="font-medium">Enabled</span>
              </label>
            </div>
          </div>

          <div class="space-y-1">
            <RuleConditionBuilder
              ref="editingRuleConditionBuilder"
              v-model="editingRule.conditions"
            />
          </div>

          <!-- Warning about unsaved conditions -->
          <div
            v-if="editingRuleHasUnsavedConditions"
            class="alert alert-warning shadow-lg"
          >
            <PhWarning :size="24" />
            <div class="flex-1">
              <h3 class="font-bold">Unsaved Conditions</h3>
              <div class="text-sm">
                Conditions have been modified but the rule has not been saved
                yet. Remember to save the rule to apply all changes.
              </div>
            </div>
            <button
              type="button"
              class="btn btn-sm btn-ghost"
              @click="restoreEditingRuleConditions()"
              title="Restore conditions to their original state"
            >
              <PhArrowCounterClockwise :size="16" />
              Restore
            </button>
          </div>
        </template>

        <template v-else-if="newRule">
          <div class="space-y-1">
            <div class="font-medium">
              Name
              <span class="text-sm text-error opacity-60 ml-1 font-normal"
                >(required)</span
              >
            </div>
            <input
              v-model="newRule.name"
              type="text"
              placeholder="Rule name"
              required
              class="input input-bordered input-sm w-full"
            />
          </div>

          <div class="space-y-1">
            <div class="font-medium">Description</div>
            <textarea
              v-model="newRule.description"
              placeholder="Rule description"
              class="textarea textarea-bordered textarea-sm w-full"
              rows="2"
            ></textarea>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div class="space-y-1">
              <div class="font-medium">Priority</div>
              <input
                v-model.number="newRule.priority"
                type="number"
                placeholder="Priority (higher = higher priority)"
                class="input input-bordered input-sm w-full"
              />
              <div class="text-sm italic opacity-70">
                Higher values have higher priority
              </div>
            </div>

            <div class="space-y-1 flex items-center">
              <label class="label cursor-pointer justify-start gap-4 p-0">
                <input
                  v-model="newRule.enabled"
                  type="checkbox"
                  class="toggle toggle-primary toggle-sm"
                />
                <span class="font-medium">Enabled</span>
              </label>
            </div>
          </div>

          <div class="space-y-1">
            <div class="font-medium mb-2">Conditions</div>
            <RuleConditionBuilder
              ref="newRuleConditionBuilder"
              v-model="newRule.conditions"
            />
          </div>

          <!-- Warning about unsaved conditions -->
          <div
            v-if="newRuleHasUnsavedConditions"
            class="alert alert-warning shadow-lg"
          >
            <PhWarning :size="24" />
            <div class="flex-1">
              <h3 class="font-bold">Unsaved Conditions</h3>
              <div class="text-sm">
                Conditions have been modified but the rule has not been saved
                yet. Remember to save the rule to apply all changes.
              </div>
            </div>
            <button
              type="button"
              class="btn btn-sm btn-ghost"
              @click="restoreNewRuleConditions()"
              title="Restore conditions to their original state"
            >
              <PhArrowCounterClockwise :size="16" />
              Restore
            </button>
          </div>
        </template>

        <div class="modal-action">
          <div v-if="ruleAddSaveError" class="flex-1 mr-auto">
            <div class="text-error text-sm">
              <span class="font-semibold">Error:</span> {{ ruleAddSaveError }}
            </div>
          </div>
          <button
            type="button"
            class="btn btn-secondary"
            @click="cancelRuleModal"
          >
            Cancel
          </button>
          <button type="submit" class="btn btn-primary">
            {{ isEditingRule ? "Save" : "Add" }}
          </button>
        </div>
      </form>
    </div>
    <form method="dialog" class="modal-backdrop">
      <button @click="cancelRuleModal">close</button>
    </form>
  </dialog>

  <!-- Copy From Rule Modal -->
  <dialog :class="['modal', { 'modal-open': showCopyFromModal }]">
    <div class="modal-box max-w-4xl">
      <h3 class="font-bold text-lg mb-4">Copy From Rule</h3>

      <div class="mb-4 flex items-center gap-4">
        <p class="text-sm opacity-70">Select a rule to copy.</p>
        <label class="label cursor-pointer gap-3 ml-auto">
          <span class="label-text font-medium">Copy only conditions</span>
          <input
            v-model="copyOnlyConditions"
            type="checkbox"
            class="toggle toggle-primary toggle-sm"
            title="Toggle between copying all rule settings or only conditions"
          />
        </label>
      </div>

      <div class="alert alert-info mb-4">
        <div class="text-sm">
          <strong v-if="copyOnlyConditions"
            >Only conditions will be copied.</strong
          >
          <strong v-else>All rule settings will be copied</strong>
          <span v-if="!copyOnlyConditions">
            (name, description, priority, enabled status, and conditions).</span
          >
        </div>
      </div>

      <!-- Search Field -->
      <div class="mb-4">
        <label
          class="input input-bordered input-sm flex items-center gap-2 w-full"
        >
          <PhMagnifyingGlass :size="16" class="opacity-70" />
          <input
            v-model="copyFromSearchQuery"
            type="text"
            placeholder="Search by policy name, rule name, description, or type..."
            class="grow"
          />
          <button
            v-if="copyFromSearchQuery"
            type="button"
            @click="copyFromSearchQuery = ''"
            class="opacity-70 hover:opacity-100"
            title="Clear search"
          >
            <PhX :size="16" />
          </button>
        </label>
      </div>

      <div class="overflow-x-auto max-h-96">
        <table class="table table-sm table-pin-rows">
          <thead>
            <tr>
              <th>Policy</th>
              <th>Type</th>
              <th>Rule Name</th>
              <th>Description</th>
              <th>Priority</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            <template v-if="filteredAvailableRules.length > 0">
              <tr
                v-for="({ policy, rule, type }, idx) in filteredAvailableRules"
                :key="`${policy.id}-${rule.id}-${idx}`"
              >
                <td>
                  <div class="font-medium">{{ policy.name }}</div>
                  <div class="text-xs opacity-50" v-if="policy.description">
                    {{ policy.description }}
                  </div>
                </td>
                <td>
                  <div
                    class="badge badge-sm"
                    :class="type === 'start' ? 'badge-success' : 'badge-error'"
                  >
                    <PhPlay v-if="type === 'start'" :size="12" />
                    <PhStop v-if="type === 'stop'" :size="12" />
                    {{ type }}
                  </div>
                </td>
                <td>
                  <div class="font-medium">{{ rule.name }}</div>
                </td>
                <td>
                  <div class="text-sm opacity-70">
                    {{ rule.description || "—" }}
                  </div>
                </td>
                <td>
                  <div class="text-sm">{{ rule.priority ?? 0 }}</div>
                </td>
                <td>
                  <div
                    class="badge badge-sm"
                    :class="rule.enabled ? 'badge-success' : 'badge-ghost'"
                  >
                    {{ rule.enabled ? "Enabled" : "Disabled" }}
                  </div>
                </td>
                <td>
                  <button
                    type="button"
                    class="btn btn-xs btn-primary"
                    @click="copyFromRule(policy, rule, type)"
                    title="Copy this rule"
                  >
                    <PhCopy :size="14" />
                    Copy
                  </button>
                </td>
              </tr>
            </template>
            <tr v-else>
              <td colspan="7" class="text-center text-base-content/50">
                {{
                  copyFromSearchQuery
                    ? "No rules found matching your search"
                    : "No rules available to copy from"
                }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="modal-action">
        <button
          type="button"
          class="btn btn-secondary"
          @click="closeCopyFromModal"
        >
          Cancel
        </button>
      </div>
    </div>
    <form method="dialog" class="modal-backdrop">
      <button @click="closeCopyFromModal">close</button>
    </form>
  </dialog>

  <!-- Policy Check Result Modal -->
  <dialog :class="['modal', { 'modal-open': showCheckModal }]">
    <div v-if="checkResult" class="modal-box max-w-2xl">
      <h3 class="font-bold text-lg mb-4">
        Policy Check: {{ checkResult.policy_name || checkingPolicyName }}
      </h3>

      <div class="flex flex-col gap-4">
        <div
          class="alert"
          :class="checkResult.valid ? 'alert-success' : 'alert-error'"
        >
          <span>{{
            checkResult.valid
              ? "Policy is valid and can be used"
              : "Policy has issues"
          }}</span>
        </div>

        <!-- Policy Statistics -->
        <div class="stats shadow">
          <div class="stat">
            <div class="stat-title">Total Start Rules</div>
            <div class="stat-value text-sm">
              {{ checkResult.start_rules_count }}
            </div>
            <div class="stat-desc">
              {{ checkResult.enabled_start_rules_count }} enabled
            </div>
          </div>

          <div class="stat">
            <div class="stat-title">Total Stop Rules</div>
            <div class="stat-value text-sm">
              {{ checkResult.stop_rules_count }}
            </div>
            <div class="stat-desc">
              {{ checkResult.enabled_stop_rules_count }} enabled
            </div>
          </div>
        </div>

        <div v-if="checkResult.errors && checkResult.errors.length > 0">
          <h4 class="font-semibold text-error mb-2">Errors:</h4>
          <ul class="list-disc list-inside">
            <li
              v-for="(error, i) in checkResult.errors"
              :key="i"
              class="text-error"
            >
              {{ error }}
            </li>
          </ul>
        </div>

        <div v-if="checkResult.warnings && checkResult.warnings.length > 0">
          <h4 class="font-semibold text-warning mb-2">Warnings:</h4>
          <ul class="list-disc list-inside">
            <li
              v-for="(warning, i) in checkResult.warnings"
              :key="i"
              class="text-warning"
            >
              {{ warning }}
            </li>
          </ul>
        </div>
      </div>

      <div class="modal-action">
        <button class="btn btn-primary" @click="closeCheckModal">Close</button>
      </div>
    </div>
    <form method="dialog" class="modal-backdrop">
      <button @click="closeCheckModal">close</button>
    </form>
  </dialog>
</template>

<style scoped></style>

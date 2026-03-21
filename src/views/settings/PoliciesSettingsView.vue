<script setup lang="ts">
import { onMounted, ref, computed } from "vue";
import { usePolicyStore } from "../../core/stores/policyStore";
import PolicyCard from "../../components/policies/PolicyCard.vue";
import PolicyFormModal from "../../components/policies/PolicyFormModal.vue";
import RuleConditionBuilder from "../../components/policies/RuleConditionBuilder.vue";
import ConfirmDialog from "../../components/ConfirmDialog.vue";
import ResourceId from "../../components/ResourceId.vue";
import type {
  OptimizationPolicy,
  AutomationRule,
  PolicyCheckResult,
  RuleType,
} from "../../core/models/policy";
import {
  PhPlus,
  PhPlay,
  PhStop,
  PhWarning,
  PhArrowCounterClockwise,
  PhCopy,
  PhMagnifyingGlass,
  PhX,
  PhGitBranch,
  PhCheckCircle,
  PhXCircle,
  PhShieldCheck,
  PhListChecks,
  PhPencil,
  PhTrash,
  PhLightningSlash,
  PhLightning,
  PhGear,
  PhFloppyDisk,
  PhTreeStructure,
} from "@phosphor-icons/vue";

const policyStore = usePolicyStore();

// Policy modal state
const showPolicyModal = ref(false);
const editingPolicy = ref<OptimizationPolicy | undefined>(undefined);
const isEditMode = ref(false);

// Rule modal state
const selectedPolicy = ref<OptimizationPolicy | undefined>(undefined);
const newRule = ref<AutomationRule | undefined>(undefined);
const editingRule = ref<AutomationRule | undefined>(undefined);
const showRulesModal = ref(false);
const showRuleEditModal = ref(false);
const isEditingRule = ref(false);
const activeRuleTab = ref<RuleType>("start");
const currentRuleType = ref<RuleType>("start");
const slideDirection = ref<"left" | "right">("right");

function switchRuleTab(tab: RuleType) {
  if (tab === activeRuleTab.value) return;
  slideDirection.value = tab === "stop" ? "left" : "right";
  activeRuleTab.value = tab;
}

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

// Rule delete confirmation
const ruleToDelete = ref<AutomationRule | null>(null);
const showRuleDeleteConfirm = ref(false);

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

// Unified active rule computed (avoids template duplication)
const activeRule = computed(() => isEditingRule.value ? editingRule.value : newRule.value);
const activeRuleHasUnsavedConditions = computed(() =>
  isEditingRule.value ? editingRuleHasUnsavedConditions.value : newRuleHasUnsavedConditions.value
);

// Stats
const stats = computed(() => {
  const policies = policyStore.policies;
  const totalPolicies = policies.length;

  let totalStartRules = 0;
  let totalStopRules = 0;
  let enabledStartRules = 0;
  let enabledStopRules = 0;

  policies.forEach((p) => {
    totalStartRules += p.start_rules?.length ?? 0;
    totalStopRules += p.stop_rules?.length ?? 0;
    enabledStartRules += p.start_rules?.filter((r) => r.enabled).length ?? 0;
    enabledStopRules += p.stop_rules?.filter((r) => r.enabled).length ?? 0;
  });

  return {
    totalPolicies,
    totalStartRules,
    totalStopRules,
    totalRules: totalStartRules + totalStopRules,
    enabledStartRules,
    enabledStopRules,
    enabledRules: enabledStartRules + enabledStopRules,
  };
});

onMounted(() => {
  policyStore.loadPolicies();
});

// Policy CRUD handlers
function openAddModal() {
  editingPolicy.value = undefined;
  isEditMode.value = false;
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
  isEditMode.value = true;
  showPolicyModal.value = true;
}

function handleCloseModal() {
  showPolicyModal.value = false;
  editingPolicy.value = undefined;
}

function handleSavePolicy(policy: OptimizationPolicy) {
  if (isEditMode.value && policy.id) {
    policyStore
      .updatePolicy(policy.id.toString(), policy)
      .then(() => {
        policyStore.loadPolicies();
        handleCloseModal();
      })
      .showToasts(
        "Policy updated successfully",
        "Failed to update policy"
      );
  } else {
    policyStore
      .addPolicy(policy)
      .then(() => {
        policyStore.loadPolicies();
        handleCloseModal();
      })
      .showToasts(
        "Policy created successfully",
        "Failed to create policy"
      );
  }
}

function handleDeletePolicy(policy: OptimizationPolicy) {
  policyStore
    .deletePolicy(policy.id!.toString())
    .then(() => {
      policyStore.loadPolicies();
    })
    .showToasts(
      "Policy deleted successfully",
      "Failed to delete policy"
    );
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

function requestDeleteRule(rule: AutomationRule) {
  ruleToDelete.value = rule;
  showRuleDeleteConfirm.value = true;
}

function cancelDeleteRule() {
  ruleToDelete.value = null;
  showRuleDeleteConfirm.value = false;
}

function handleDeleteRule(rule: AutomationRule) {
  showRuleDeleteConfirm.value = false;
  ruleToDelete.value = null;
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

function restoreActiveRuleConditions() {
  if (isEditingRule.value) restoreEditingRuleConditions();
  else restoreNewRuleConditions();
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
    targetRule.conditions = JSON.parse(JSON.stringify(sourceRule.conditions));
  } else {
    const targetId = targetRule.id;
    Object.assign(targetRule, {
      ...sourceRule,
      id: targetId,
      conditions: JSON.parse(JSON.stringify(sourceRule.conditions)),
    });
  }

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
  <div class="card">
    <div class="card-header">
      <!-- Header -->
      <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <h1 class="text-2xl font-bold text-base-content">Optimization Policies</h1>
          <p class="text-sm text-base-content/60 mt-1">
            Define automation rules that control mining start/stop behavior
          </p>
        </div>

        <button class="btn btn-primary gap-2" @click="openAddModal">
          <PhPlus :size="20" weight="bold" />
          Add Policy
        </button>
      </div>
    </div>
    <div class="card-body">
      <div class="space-y-6">
        <!-- Stats Cards -->
        <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3 sm:gap-4">
          <div class="stat-card bg-neutral-800/80 border border-base-300/40 rounded-xl p-3 sm:p-4 min-w-0">
            <div class="stat-value text-primary flex items-center gap-2">
              {{ stats.totalPolicies }}
              <PhGitBranch :size="20" class="opacity-60" />
            </div>
            <div class="stat-label">Policies</div>
          </div>
          <div class="stat-card bg-neutral-800/80 border border-base-300/40 rounded-xl p-3 sm:p-4 min-w-0">
            <div class="stat-value text-base-content flex items-center gap-2">
              {{ stats.totalRules }}
              <PhListChecks :size="20" class="opacity-40" />
            </div>
            <div class="stat-label">Total Rules</div>
          </div>
          <div class="stat-card bg-neutral-800/80 border border-base-300/40 rounded-xl p-3 sm:p-4 min-w-0">
            <div class="flex gap-4 items-center min-h-[2rem] sm:min-h-[2.25rem]">
              <div class="flex items-center gap-1.5">
                <PhPlay :size="16" class="text-primary" weight="fill" />
                <span class="stat-type-count text-primary">{{ stats.totalStartRules }}</span>
              </div>
              <div class="flex items-center gap-1.5">
                <PhStop :size="16" class="text-rose-300" weight="fill" />
                <span class="stat-type-count text-rose-300">{{ stats.totalStopRules }}</span>
              </div>
            </div>
            <div class="stat-label">Start / Stop</div>
          </div>
          <div class="stat-card bg-neutral-800/80 border border-base-300/40 rounded-xl p-3 sm:p-4 min-w-0">
            <div class="stat-value text-primary flex items-center gap-2">
              {{ stats.enabledRules }}
              <PhCheckCircle :size="20" class="opacity-60" />
            </div>
            <div class="stat-label">Enabled Rules</div>
          </div>
        </div>

        <!-- Cards Grid -->
        <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          <PolicyCard
            v-for="policy in policyStore.policies"
            :key="policy.id"
            :policy="policy"
            @edit="handleEditPolicy"
            @delete="handleDeletePolicy"
            @manage-rules="handleManageRules"
            @check="handleCheckPolicy"
          />

          <!-- Empty State -->
          <div
            v-if="policyStore.policies.length === 0"
            class="col-span-full flex flex-col items-center justify-center py-16 text-center"
          >
            <div
              class="w-20 h-20 rounded-full bg-base-200 flex items-center justify-center mb-4"
            >
              <PhGitBranch :size="40" class="text-base-content/30" />
            </div>
            <h3 class="text-lg font-semibold text-base-content/80">
              No policies yet
            </h3>
            <p class="text-sm text-base-content/50 mt-1 max-w-sm">
              Create your first optimization policy to automate mining start/stop decisions.
            </p>
            <button
              class="btn btn-primary btn-sm mt-4 gap-2"
              @click="openAddModal"
            >
              <PhPlus :size="16" />
              Add Policy
            </button>
          </div>
        </div>

        <!-- Policy Form Modal -->
        <PolicyFormModal
          :open="showPolicyModal"
          :policy="editingPolicy"
          :is-edit="isEditMode"
          @close="handleCloseModal"
          @save="handleSavePolicy"
        />
      </div>
    </div>
  </div>

  <!-- Rules Management Modal -->
  <dialog :class="['modal', { 'modal-open': showRulesModal }]">
    <div v-if="selectedPolicy" class="modal-box max-w-4xl bg-base-100 border border-base-300/60 p-0 overflow-hidden">
      <!-- Modal Header -->
      <div class="px-6 pt-6 pb-4 border-b border-base-300/40">
        <div class="flex items-start justify-between gap-4">
          <div class="flex items-center gap-3 min-w-0">
            <div class="h-11 w-11 rounded-xl bg-indigo-500/15 flex items-center justify-center flex-shrink-0">
              <PhGitBranch :size="24" class="text-indigo-400" weight="duotone" />
            </div>
            <div class="min-w-0">
              <h3 class="text-lg font-bold text-base-content truncate">{{ selectedPolicy.name }}</h3>
              <p v-if="selectedPolicy.description" class="text-sm text-base-content/50 truncate mt-0.5">{{ selectedPolicy.description }}</p>
            </div>
          </div>
          <button class="btn btn-ghost btn-sm btn-square flex-shrink-0" @click="closeRulesModal">
            <PhX :size="20" />
          </button>
        </div>

        <!-- Mini stats -->
        <div class="flex items-center gap-4 mt-4">
          <div class="flex items-center gap-1.5 text-sm">
            <PhPlay :size="14" class="text-primary" weight="fill" />
            <span class="font-semibold text-primary">{{ selectedPolicy.start_rules?.length ?? 0 }}</span>
            <span class="text-base-content/40">start</span>
          </div>
          <div class="flex items-center gap-1.5 text-sm">
            <PhStop :size="14" class="text-rose-300" weight="fill" />
            <span class="font-semibold text-rose-300">{{ selectedPolicy.stop_rules?.length ?? 0 }}</span>
            <span class="text-base-content/40">stop</span>
          </div>
          <div class="flex items-center gap-1.5 text-sm ml-auto">
            <PhCheckCircle :size="14" class="text-primary/60" />
            <span class="text-base-content/50">{{ (selectedPolicy.start_rules?.filter(r => r.enabled).length ?? 0) + (selectedPolicy.stop_rules?.filter(r => r.enabled).length ?? 0) }} enabled</span>
          </div>
        </div>
      </div>

      <!-- Tab Switcher -->
      <div class="px-6 pt-4">
        <div class="relative flex bg-base-200/60 rounded-lg p-1 gap-1">
          <!-- Sliding indicator -->
          <div
            class="tab-indicator absolute top-1 bottom-1 rounded-md transition-all duration-300 ease-in-out"
            :class="activeRuleTab === 'start'
              ? 'bg-primary/20 border border-primary/30 shadow-sm'
              : 'bg-rose-300/20 border border-rose-300/30 shadow-sm'"
            :style="{ left: activeRuleTab === 'start' ? 'calc(0.25rem)' : 'calc(50% + 0.125rem)', width: 'calc(50% - 0.375rem)' }"
          ></div>
          <button
            class="relative z-[1] flex-1 flex items-center justify-center gap-2 rounded-md py-2 px-3 text-sm font-medium transition-colors duration-200 cursor-pointer"
            :class="activeRuleTab === 'start'
              ? 'text-primary'
              : 'text-base-content/50 hover:text-base-content/80'"
            @click="switchRuleTab('start')"
          >
            <PhPlay :size="16" weight="fill" />
            Start Rules
            <span class="badge badge-sm" :class="activeRuleTab === 'start' ? 'bg-primary/30 text-primary border-0' : 'badge-ghost'">
              {{ selectedPolicy.start_rules?.length ?? 0 }}
            </span>
          </button>
          <button
            class="relative z-[1] flex-1 flex items-center justify-center gap-2 rounded-md py-2 px-3 text-sm font-medium transition-colors duration-200 cursor-pointer"
            :class="activeRuleTab === 'stop'
              ? 'text-rose-300'
              : 'text-base-content/50 hover:text-base-content/80'"
            @click="switchRuleTab('stop')"
          >
            <PhStop :size="16" weight="fill" />
            Stop Rules
            <span class="badge badge-sm" :class="activeRuleTab === 'stop' ? 'bg-rose-300/30 text-rose-300 border-0' : 'badge-ghost'">
              {{ selectedPolicy.stop_rules?.length ?? 0 }}
            </span>
          </button>
        </div>
      </div>

      <!-- Rules List -->
      <div class="px-6 py-4 max-h-[50vh] overflow-y-auto overflow-x-hidden rules-scroll">
        <Transition :name="slideDirection === 'left' ? 'slide-left' : 'slide-right'" mode="out-in">
        <!-- Start Rules Tab -->
        <div v-if="activeRuleTab === 'start'" key="start" class="space-y-2">
          <template v-if="selectedPolicy.start_rules && selectedPolicy.start_rules.length > 0">
            <div
              v-for="rule in selectedPolicy.start_rules"
              :key="rule.id"
              class="rule-card group/rule flex items-center gap-3 rounded-lg border border-base-300/40 p-3 transition-all duration-200 hover:border-primary/30 hover:bg-primary/5"
            >
              <!-- Toggle -->
              <div class="flex-shrink-0">
                <input
                  type="checkbox"
                  class="toggle toggle-success toggle-sm"
                  :checked="rule.enabled"
                  @change="handleToggleRuleEnabled(rule)"
                  title="Toggle rule enabled/disabled"
                />
              </div>

              <!-- Rule Info -->
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2">
                  <span class="font-semibold text-sm text-base-content truncate">{{ rule.name }}</span>
                  <ResourceId v-if="rule.id" :id="rule.id" />
                </div>
                <p class="text-xs text-base-content/40 truncate mt-0.5">
                  {{ rule.description || 'No description' }}
                </p>
              </div>

              <!-- Status indicator -->
              <div class="flex-shrink-0">
                <span
                  v-if="rule.enabled"
                  class="badge badge-sm bg-primary/20 text-primary border-0 gap-1"
                >
                  <span class="w-1.5 h-1.5 rounded-full bg-primary"></span>
                  Active
                </span>
                <span v-else class="badge badge-sm badge-ghost gap-1">
                  <PhLightningSlash :size="10" />
                  Disabled
                </span>
              </div>

              <!-- Priority -->
              <div class="flex-shrink-0">
                <div
                  class="flex items-center gap-1 rounded-md bg-base-200/60 px-2 py-1 text-xs font-mono"
                  :title="`Priority: ${rule.priority ?? 0}`"
                >
                  <PhLightning :size="12" class="text-amber-400/70" />
                  <span class="text-base-content/60">{{ rule.priority ?? 0 }}</span>
                </div>
              </div>

              <!-- Actions -->
              <div class="flex gap-1 opacity-0 group-hover/rule:opacity-100 transition-opacity flex-shrink-0">
                <button
                  class="btn btn-ghost btn-sm btn-square hover:bg-primary/20"
                  title="Edit rule"
                  @click="handleEditRule(rule, 'start')"
                >
                  <PhPencil :size="14" class="text-primary" />
                </button>
                <button
                  class="btn btn-ghost btn-sm btn-square hover:bg-error/20"
                  title="Delete rule"
                  @click="requestDeleteRule(rule)"
                >
                  <PhTrash :size="14" class="text-error" />
                </button>
              </div>
            </div>
          </template>

          <!-- Empty Start Rules -->
          <div v-else class="flex flex-col items-center justify-center py-10 text-center">
            <div class="w-14 h-14 rounded-full bg-primary/10 flex items-center justify-center mb-3">
              <PhPlay :size="28" class="text-primary/40" />
            </div>
            <p class="text-sm font-medium text-base-content/60">No start rules defined</p>
            <p class="text-xs text-base-content/35 mt-1">Add a start rule to automate mining activation</p>
          </div>
        </div>

        <!-- Stop Rules Tab -->
        <div v-else key="stop" class="space-y-2">
          <template v-if="selectedPolicy.stop_rules && selectedPolicy.stop_rules.length > 0">
            <div
              v-for="rule in selectedPolicy.stop_rules"
              :key="rule.id"
              class="rule-card group/rule flex items-center gap-3 rounded-lg border border-base-300/40 p-3 transition-all duration-200 hover:border-rose-300/30 hover:bg-rose-300/5"
            >
              <!-- Toggle -->
              <div class="flex-shrink-0">
                <input
                  type="checkbox"
                  class="toggle toggle-error toggle-sm"
                  :checked="rule.enabled"
                  @change="handleToggleRuleEnabled(rule)"
                  title="Toggle rule enabled/disabled"
                />
              </div>

              <!-- Rule Info -->
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2">
                  <span class="font-semibold text-sm text-base-content truncate">{{ rule.name }}</span>
                  <ResourceId v-if="rule.id" :id="rule.id" />
                </div>
                <p class="text-xs text-base-content/40 truncate mt-0.5">
                  {{ rule.description || 'No description' }}
                </p>
              </div>

              <!-- Status indicator -->
              <div class="flex-shrink-0">
                <span
                  v-if="rule.enabled"
                  class="badge badge-sm bg-rose-300/20 text-rose-300 border-0 gap-1"
                >
                  <span class="w-1.5 h-1.5 rounded-full bg-rose-300"></span>
                  Active
                </span>
                <span v-else class="badge badge-sm badge-ghost gap-1">
                  <PhLightningSlash :size="10" />
                  Disabled
                </span>
              </div>

              <!-- Priority -->
              <div class="flex-shrink-0">
                <div
                  class="flex items-center gap-1 rounded-md bg-base-200/60 px-2 py-1 text-xs font-mono"
                  :title="`Priority: ${rule.priority ?? 0}`"
                >
                  <PhLightning :size="12" class="text-amber-400/70" />
                  <span class="text-base-content/60">{{ rule.priority ?? 0 }}</span>
                </div>
              </div>

              <!-- Actions -->
              <div class="flex gap-1 opacity-0 group-hover/rule:opacity-100 transition-opacity flex-shrink-0">
                <button
                  class="btn btn-ghost btn-sm btn-square hover:bg-primary/20"
                  title="Edit rule"
                  @click="handleEditRule(rule, 'stop')"
                >
                  <PhPencil :size="14" class="text-primary" />
                </button>
                <button
                  class="btn btn-ghost btn-sm btn-square hover:bg-error/20"
                  title="Delete rule"
                  @click="requestDeleteRule(rule)"
                >
                  <PhTrash :size="14" class="text-error" />
                </button>
              </div>
            </div>
          </template>

          <!-- Empty Stop Rules -->
          <div v-else class="flex flex-col items-center justify-center py-10 text-center">
            <div class="w-14 h-14 rounded-full bg-rose-300/10 flex items-center justify-center mb-3">
              <PhStop :size="28" class="text-rose-300/40" />
            </div>
            <p class="text-sm font-medium text-base-content/60">No stop rules defined</p>
            <p class="text-xs text-base-content/35 mt-1">Add a stop rule to automate mining shutdown</p>
          </div>
        </div>
        </Transition>
      </div>

      <!-- Footer -->
      <div class="px-6 py-4 border-t border-base-300/40 bg-base-200/20">
        <div v-if="ruleDeleteError" class="mb-3">
          <div class="rounded-lg bg-error/10 border border-error/20 px-3 py-2 text-sm text-error flex items-center gap-2">
            <PhXCircle :size="16" class="flex-shrink-0" />
            <span>{{ ruleDeleteError }}</span>
          </div>
        </div>
        <div class="flex items-center justify-end gap-2">
          <button class="btn btn-ghost" @click="closeRulesModal">
            Close
          </button>
          <button
            class="btn gap-2"
            :class="activeRuleTab === 'start' ? 'btn-primary' : 'bg-rose-300/50 text-primary-content hover:bg-rose-300/47'"
            @click="addRule"
          >
            <PhPlus :size="16" weight="bold" />
            Add {{ activeRuleTab === "start" ? "Start" : "Stop" }} Rule
          </button>
        </div>
      </div>
    </div>
    <form method="dialog" class="modal-backdrop bg-black/50">
      <button @click="closeRulesModal">close</button>
    </form>
  </dialog>

  <!-- Rule Delete Confirmation -->
  <ConfirmDialog
    :open="showRuleDeleteConfirm"
    title="Delete Rule"
    :message="`Are you sure you want to delete rule '${ruleToDelete?.name ?? ''}'?`"
    confirm-text="Delete"
    variant="danger"
    @confirm="() => { if (ruleToDelete) handleDeleteRule(ruleToDelete); }"
    @cancel="cancelDeleteRule"
  />

  <!-- Rule Add/Edit Modal -->
  <dialog :class="['modal', { 'modal-open': showRuleEditModal }]">
    <div v-if="activeRule" class="modal-box max-w-5xl bg-base-100 border border-base-300/60 p-0 overflow-hidden flex flex-col max-h-[85vh]">
      <!-- Header -->
      <div class="px-6 pt-6 pb-4 border-b border-base-300/40 flex-shrink-0">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div
              class="h-11 w-11 rounded-xl flex items-center justify-center flex-shrink-0"
              :class="currentRuleType === 'start' ? 'bg-primary/15' : 'bg-rose-300/15'"
            >
              <PhPlay v-if="currentRuleType === 'start'" :size="24" class="text-primary" weight="duotone" />
              <PhStop v-else :size="24" class="text-rose-300" weight="duotone" />
            </div>
            <div class="min-w-0">
              <h3 class="text-xl font-bold text-base-content">
                {{ isEditingRule ? 'Edit' : 'Add' }}
                {{ currentRuleType === 'start' ? 'Start' : 'Stop' }} Rule
              </h3>
              <p v-if="selectedPolicy" class="text-sm text-base-content/50 truncate mt-0.5">
                {{ selectedPolicy.name }}
              </p>
            </div>
          </div>
          <button class="btn btn-ghost btn-sm btn-square flex-shrink-0" @click="cancelRuleModal">
            <PhX :size="20" />
          </button>
        </div>
      </div>

      <!-- Scrollable Body -->
      <div class="flex-1 overflow-y-auto px-6 py-5 space-y-6 rules-scroll">
        <!-- Required fields note -->
        <p class="text-xs text-base-content/50">* Required fields</p>

        <!-- Basic Information Section -->
        <div class="space-y-4">
          <div class="flex items-center gap-2 text-sm font-semibold text-base-content/70 uppercase tracking-wider">
            <PhGear :size="16" />
            Basic Information
          </div>

          <!-- Name Input -->
          <div class="form-control">
            <label class="label mb-1">
              <span class="label-text font-medium">Name *</span>
            </label>
            <input
              v-model="activeRule.name"
              type="text"
              placeholder="Enter rule name"
              class="input input-bordered w-full"
              required
            />
          </div>

          <!-- Description -->
          <div class="form-control">
            <label class="label mb-1">
              <span class="label-text font-medium">Description</span>
            </label>
            <textarea
              v-model="activeRule.description"
              placeholder="Brief description of this rule"
              class="textarea textarea-bordered w-full resize-none"
              rows="2"
            ></textarea>
          </div>
        </div>

        <!-- Priority & Status Section -->
        <div class="space-y-4">
          <div class="flex items-center gap-2 text-sm font-semibold text-base-content/70 uppercase tracking-wider">
            <PhLightning :size="16" />
            Priority & Status
          </div>

          <div class="bg-base-200/50 rounded-xl p-4 border border-base-300/40">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 items-center">
              <!-- Priority Input -->
              <div class="form-control">
                <label class="label mb-1">
                  <span class="label-text font-medium">Priority</span>
                </label>
                <div class="relative">
                  <input
                    v-model.number="activeRule.priority"
                    type="number"
                    placeholder="10"
                    class="input input-bordered w-full pl-9"
                  />
                  <PhLightning :size="16" class="absolute left-3 top-1/2 -translate-y-1/2 text-amber-400/70" />
                </div>
                <label class="label">
                  <span class="label-text-alt text-base-content/50 italic">Higher values = higher priority</span>
                </label>
              </div>

              <!-- Enabled Toggle -->
              <div class="flex items-center justify-between md:justify-start md:gap-6 bg-base-300/30 rounded-lg px-4 py-3">
                <label class="cursor-pointer flex items-center gap-3">
                  <input
                    v-model="activeRule.enabled"
                    type="checkbox"
                    class="toggle"
                    :class="currentRuleType === 'start' ? 'toggle-success' : 'toggle-error'"
                  />
                  <span class="font-medium">Enabled</span>
                </label>
              </div>
            </div>
          </div>
        </div>

        <!-- Conditions Section -->
        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2 text-sm font-semibold text-base-content/70 uppercase tracking-wider">
              <PhTreeStructure :size="16" />
              Conditions
            </div>
            <button
              type="button"
              class="btn btn-ghost btn-xs gap-1.5 text-base-content/60 hover:text-base-content"
              @click="openCopyFromModal(isEditingRule ? 'editing' : 'new')"
              title="Copy conditions from another rule"
            >
              <PhCopy :size="14" />
              Copy From
            </button>
          </div>

          <div class="bg-base-200/30 rounded-xl p-4 border border-base-300/40">
            <RuleConditionBuilder
              v-if="isEditingRule"
              ref="editingRuleConditionBuilder"
              v-model="activeRule.conditions"
            />
            <RuleConditionBuilder
              v-else
              ref="newRuleConditionBuilder"
              v-model="activeRule.conditions"
            />
          </div>
        </div>

        <!-- Unsaved Conditions Warning -->
        <div
          v-if="activeRuleHasUnsavedConditions"
          class="rounded-xl bg-warning/10 border border-warning/20 px-4 py-3 flex items-center gap-3"
        >
          <PhWarning :size="20" class="text-warning flex-shrink-0" />
          <div class="flex-1 min-w-0">
            <p class="font-semibold text-sm text-warning">Unsaved Conditions</p>
            <p class="text-xs text-base-content/50 mt-0.5">
              Conditions have been modified. Save the rule to apply changes.
            </p>
          </div>
          <button
            type="button"
            class="btn btn-ghost btn-xs gap-1"
            @click="restoreActiveRuleConditions"
            title="Restore conditions to original state"
          >
            <PhArrowCounterClockwise :size="14" />
            Restore
          </button>
        </div>
      </div>

      <!-- Footer -->
      <div class="px-6 py-4 border-t border-base-300/40 bg-base-200/20 flex-shrink-0">
        <div v-if="ruleAddSaveError" class="mb-3">
          <div class="rounded-lg bg-error/10 border border-error/20 px-3 py-2 text-sm text-error flex items-center gap-2">
            <PhXCircle :size="16" class="flex-shrink-0" />
            <span>{{ ruleAddSaveError }}</span>
          </div>
        </div>
        <div class="flex items-center justify-end gap-3">
          <button type="button" class="btn btn-ghost" @click="cancelRuleModal">
            Cancel
          </button>
          <button
            type="button"
            class="btn gap-2"
            :class="currentRuleType === 'start' ? 'btn-primary' : 'bg-rose-300/80 text-primary-content hover:bg-rose-300/70'"
            :disabled="!activeRule.name?.trim()"
            @click="isEditingRule ? confirmEditRule() : confirmAddRule()"
          >
            <PhFloppyDisk :size="18" />
            {{ isEditingRule ? 'Save Changes' : 'Create Rule' }}
          </button>
        </div>
      </div>
    </div>
    <form method="dialog" class="modal-backdrop bg-black/50">
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
          <input v-model="copyOnlyConditions" type="checkbox" class="toggle toggle-primary toggle-sm"
            title="Toggle between copying all rule settings or only conditions" />
        </label>
      </div>

      <div class="alert alert-info mb-4">
        <div class="text-sm">
          <strong v-if="copyOnlyConditions">Only conditions will be copied.</strong>
          <strong v-else>All rule settings will be copied</strong>
          <span v-if="!copyOnlyConditions">
            (name, description, priority, enabled status, and conditions).</span>
        </div>
      </div>

      <!-- Search Field -->
      <div class="mb-4">
        <label class="input input-bordered input-sm flex items-center gap-2 w-full">
          <PhMagnifyingGlass :size="16" class="opacity-70" />
          <input v-model="copyFromSearchQuery" type="text"
            placeholder="Search by policy name, rule name, description, or type..." class="grow" />
          <button v-if="copyFromSearchQuery" type="button" @click="copyFromSearchQuery = ''"
            class="opacity-70 hover:opacity-100" title="Clear search">
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
              <tr v-for="({ policy, rule, type }, idx) in filteredAvailableRules"
                :key="`${policy.id}-${rule.id}-${idx}`">
                <td>
                  <div class="font-medium">{{ policy.name }}</div>
                  <div class="text-xs opacity-50" v-if="policy.description">
                    {{ policy.description }}
                  </div>
                </td>
                <td>
                  <div class="badge badge-sm" :class="type === 'start' ? 'badge-success' : 'badge-error'">
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
                  <div class="badge badge-sm" :class="rule.enabled ? 'badge-success' : 'badge-ghost'">
                    {{ rule.enabled ? "Enabled" : "Disabled" }}
                  </div>
                </td>
                <td>
                  <button type="button" class="btn btn-xs btn-primary" @click="copyFromRule(policy, rule, type)"
                    title="Copy this rule">
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

      <div class="flex justify-end gap-3 pt-4 border-t border-base-300/40 mt-4">
        <button type="button" class="btn btn-ghost" @click="closeCopyFromModal">
          Cancel
        </button>
      </div>
    </div>
    <form method="dialog" class="modal-backdrop">
      <button @click="closeCopyFromModal">close</button>
    </form>
  </dialog>

  <!-- Policy Check Result Modal -->
  <dialog class="modal" :class="{ 'modal-open': showCheckModal }">
    <div v-if="checkResult" class="modal-box max-w-2xl bg-base-100 border border-base-300/60">
      <!-- Header -->
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center gap-3">
          <div class="h-10 w-10 rounded-xl bg-base-200/60 flex items-center justify-center">
            <PhShieldCheck :size="22" class="text-indigo-400" />
          </div>
          <div>
            <h3 class="text-lg font-bold">Policy Check</h3>
            <p class="text-sm text-base-content/60">{{ checkResult.policy_name || checkingPolicyName }}</p>
          </div>
        </div>
        <button class="btn btn-ghost btn-sm btn-square" @click="closeCheckModal">
          <PhX :size="20" />
        </button>
      </div>

      <div class="space-y-4">
        <!-- Validity Status -->
        <div
          class="flex flex-col items-center gap-3 py-6"
        >
          <div
            class="w-16 h-16 rounded-full flex items-center justify-center"
            :class="checkResult.valid ? 'bg-success/20' : 'bg-error/20'"
          >
            <PhCheckCircle v-if="checkResult.valid" :size="36" class="text-success" />
            <PhXCircle v-else :size="36" class="text-error" />
          </div>
          <p
            class="text-lg font-semibold"
            :class="checkResult.valid ? 'text-success' : 'text-error'"
          >
            {{ checkResult.valid ? "Policy is Valid" : "Policy Has Issues" }}
          </p>
        </div>

        <!-- Rule Stats -->
        <div class="grid grid-cols-2 gap-3">
          <div class="flex flex-col items-center gap-1 rounded-lg bg-primary/10 border border-primary/20 p-3">
            <div class="flex items-center gap-1.5">
              <PhPlay :size="14" class="text-primary" weight="fill" />
              <span class="text-xl font-bold text-primary">{{ checkResult.start_rules_count }}</span>
            </div>
            <span class="text-[11px] text-primary/70 uppercase tracking-wider">Start Rules</span>
            <span class="text-[10px] text-base-content/40">{{ checkResult.enabled_start_rules_count }} enabled</span>
          </div>
          <div class="flex flex-col items-center gap-1 rounded-lg bg-rose-300/10 border border-rose-300/20 p-3">
            <div class="flex items-center gap-1.5">
              <PhStop :size="14" class="text-rose-300" weight="fill" />
              <span class="text-xl font-bold text-rose-300">{{ checkResult.stop_rules_count }}</span>
            </div>
            <span class="text-[11px] text-rose-300/70 uppercase tracking-wider">Stop Rules</span>
            <span class="text-[10px] text-base-content/40">{{ checkResult.enabled_stop_rules_count }} enabled</span>
          </div>
        </div>

        <!-- Errors -->
        <div v-if="checkResult.errors && checkResult.errors.length > 0" class="space-y-2">
          <h4 class="font-semibold text-error text-sm flex items-center gap-2">
            <PhXCircle :size="16" />
            Errors ({{ checkResult.errors.length }})
          </h4>
          <div
            v-for="(error, i) in checkResult.errors"
            :key="i"
            class="rounded-lg bg-error/10 border border-error/20 px-3 py-2 text-sm text-error"
          >
            {{ error }}
          </div>
        </div>

        <!-- Warnings -->
        <div v-if="checkResult.warnings && checkResult.warnings.length > 0" class="space-y-2">
          <h4 class="font-semibold text-warning text-sm flex items-center gap-2">
            <PhWarning :size="16" />
            Warnings ({{ checkResult.warnings.length }})
          </h4>
          <div
            v-for="(warning, i) in checkResult.warnings"
            :key="i"
            class="rounded-lg bg-warning/10 border border-warning/20 px-3 py-2 text-sm text-warning"
          >
            {{ warning }}
          </div>
        </div>
      </div>

      <div class="flex justify-end pt-4 border-t border-base-300/40 mt-4">
        <button class="btn btn-primary btn-sm" @click="closeCheckModal">Close</button>
      </div>
    </div>
    <form method="dialog" class="modal-backdrop bg-black/50">
      <button @click="closeCheckModal">close</button>
    </form>
  </dialog>
</template>

<style scoped>
.stat-card {
  transition: all 0.2s ease;
}

.stat-card:hover {
  border-color: oklch(50% 0 0 / 0.5);
}

.stat-value {
  font-weight: 700;
  font-size: clamp(1.25rem, 4vw, 1.875rem);
  line-height: 1.2;
}

.stat-label {
  font-size: clamp(0.7rem, 2vw, 0.875rem);
  color: oklch(80% 0 0 / 0.6);
  margin-top: 0.125rem;
}

.rule-card {
  background-color: oklch(28% 0 0 / 0.6);
}

.rules-scroll::-webkit-scrollbar {
  width: 6px;
}

.rules-scroll::-webkit-scrollbar-track {
  background: transparent;
}

.rules-scroll::-webkit-scrollbar-thumb {
  background: oklch(50% 0 0 / 0.3);
  border-radius: 3px;
}

.rules-scroll::-webkit-scrollbar-thumb:hover {
  background: oklch(50% 0 0 / 0.5);
}

/* Slide left: content exits left, new enters from right */
.slide-left-enter-active,
.slide-left-leave-active,
.slide-right-enter-active,
.slide-right-leave-active {
  transition: all 0.25s ease;
}

.slide-left-enter-from {
  opacity: 0;
  transform: translateX(30px);
}
.slide-left-leave-to {
  opacity: 0;
  transform: translateX(-30px);
}

.slide-right-enter-from {
  opacity: 0;
  transform: translateX(-30px);
}
.slide-right-leave-to {
  opacity: 0;
  transform: translateX(30px);
}
</style>

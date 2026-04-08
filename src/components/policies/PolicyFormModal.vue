<script setup lang="ts">
import { computed, ref, watch } from "vue";
import type { OptimizationPolicy } from "../../core/models/policy";
import {
  PhX,
  PhFloppyDisk,
  PhGitBranch,
  PhGear,
  PhUser,
  PhTag,
} from "@phosphor-icons/vue";

const props = defineProps<{
  open: boolean;
  policy?: OptimizationPolicy;
  isEdit?: boolean;
}>();

const emit = defineEmits<{
  close: [];
  save: [policy: OptimizationPolicy];
}>();

// Local form state
const formData = ref<OptimizationPolicy>({
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
});

// Watch for modal open to reset form
watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) {
      if (props.policy) {
        formData.value = {
          ...props.policy,
          metadata: props.policy.metadata
            ? { ...props.policy.metadata }
            : {
                author: undefined,
                version: undefined,
                created: undefined,
                last_modified: undefined,
              },
        };
      } else {
        formData.value = {
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
      }
    }
  },
  { immediate: true }
);

const isFormValid = computed(() => {
  return formData.value.name.trim().length > 0;
});

function handleClose() {
  emit("close");
}

function handleSave() {
  if (isFormValid.value) {
    emit("save", { ...formData.value });
  }
}

function formatDate(date?: string): string {
  if (!date) return "—";
  try {
    return new Date(date).toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return date;
  }
}
</script>

<template>
  <dialog class="modal" :class="{ 'modal-open': open }">
    <div class="modal-box max-w-2xl bg-base-100 border border-base-300/60">
      <!-- Header -->
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center gap-3">
          <div class="h-10 w-10 rounded-xl bg-base-200/60 flex items-center justify-center">
            <PhGitBranch :size="22" class="text-indigo-400" />
          </div>
          <h3 class="text-xl font-bold">
            {{ isEdit ? "Edit Policy" : "Add Policy" }}
          </h3>
        </div>
        <button class="btn btn-ghost btn-sm btn-square" @click="handleClose">
          <PhX :size="20" />
        </button>
      </div>

      <!-- Required fields note -->
      <p class="text-xs text-base-content/50 mb-4">* Required fields</p>

      <!-- Form -->
      <form class="space-y-6" @submit.prevent="handleSave">
        <!-- Basic Info Section -->
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
              v-model="formData.name"
              type="text"
              placeholder="Enter policy name"
              class="input input-bordered w-full"
              required
            />
          </div>

          <!-- Description Textarea -->
          <div class="form-control">
            <label class="label mb-1">
              <span class="label-text font-medium">Description</span>
            </label>
            <textarea
              v-model="formData.description"
              placeholder="Describe the policy's purpose and behavior..."
              class="textarea textarea-bordered w-full"
              rows="3"
            ></textarea>
          </div>
        </div>

        <!-- Metadata Section (only visible when editing) -->
        <div v-if="isEdit && formData.metadata" class="space-y-4">
          <div class="flex items-center gap-2 text-sm font-semibold text-base-content/70 uppercase tracking-wider">
            <PhTag :size="16" />
            Metadata
          </div>

          <div class="bg-base-200/50 rounded-xl p-4 border border-base-300/40">
            <div class="grid grid-cols-2 gap-4">
              <div class="flex items-center gap-2">
                <PhUser :size="16" class="text-base-content/40" />
                <div>
                  <div class="text-[10px] uppercase tracking-wider text-base-content/40">Author</div>
                  <div class="text-sm">{{ formData.metadata.author || "—" }}</div>
                </div>
              </div>
              <div class="flex items-center gap-2">
                <PhTag :size="16" class="text-base-content/40" />
                <div>
                  <div class="text-[10px] uppercase tracking-wider text-base-content/40">Version</div>
                  <div class="text-sm">{{ formData.metadata.version ? `v${formData.metadata.version}` : "—" }}</div>
                </div>
              </div>
              <div>
                <div class="text-[10px] uppercase tracking-wider text-base-content/40">Created</div>
                <div class="text-sm">{{ formatDate(formData.metadata.created) }}</div>
              </div>
              <div>
                <div class="text-[10px] uppercase tracking-wider text-base-content/40">Last Modified</div>
                <div class="text-sm">{{ formatDate(formData.metadata.last_modified) }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Actions -->
        <div class="flex justify-end gap-3 pt-4 border-t border-base-300/40">
          <button type="button" class="btn btn-ghost" @click="handleClose">
            Cancel
          </button>
          <button
            type="submit"
            class="btn btn-primary gap-2"
            :disabled="!isFormValid"
          >
            <PhFloppyDisk :size="18" />
            {{ isEdit ? "Save Changes" : "Create Policy" }}
          </button>
        </div>
      </form>
    </div>

    <!-- Backdrop -->
    <form method="dialog" class="modal-backdrop bg-black/50">
      <button @click="handleClose">close</button>
    </form>
  </dialog>
</template>

<style scoped>
.space-y-4:hover .uppercase {
  color: oklch(var(--bc) / 0.8);
}
</style>

import { defineStore } from "pinia";
import { computed, ref, watch } from "vue";
import router from "../../router";
import { useLoader } from "../composables/useLoader";
import type { UserNotification } from "../models/userNotification";

export const useAppStore = defineStore("app", () => {
  // STATE
  const userNotification = ref<UserNotification>();
  const version = ref<string>("");
  const versionLoading = ref(true);
  // The state bound to the loader shown in the App.vue component. Can be used by any component or service that needs to put
  // the user on hold.
  const loader = useLoader();

  // GETTERS
  const rootUrl = computed(
    () => import.meta.env.VITE_API_BASE_URL || "" // Use .env variable or default to relative path
  );
  const apiUrl = computed(() => rootUrl.value + "/api/v1");

  // ACTIONS
  function showToast(notification: UserNotification, extra?: string) {
    console.info(
      `Firing ${notification.status} Toast:`,
      notification.message,
      extra
    );
    userNotification.value = notification;
    setTimeout(() => {
      userNotification.value = undefined;
    }, 4000);
  }

  function showSuccessToast(message: string) {
    showToast({ status: "success", message });
  }

  function showWarningToast(message: string) {
    showToast({ status: "warning", message });
  }

  function showInfoToast(message: string) {
    showToast({ status: "info", message });
  }

  function showErrorToast(message: string, reason?: any) {
    showToast({ status: "error", message }, reason);
  }

  async function fetchVersion() {
    versionLoading.value = true;
    try {
      const response = await fetch(`${rootUrl.value}/api/version`);
      if (response.ok) {
        const data = await response.json();
        version.value = data.version;
      }
    } catch (error) {
      console.error("Failed to fetch version:", error);
    } finally {
      versionLoading.value = false;
    }
  }

  function updateDocumentTitle() {
    let title = `Edge Mining`;
    const routeTitle = router.currentRoute.value.meta?.title;
    if (routeTitle) {
      title += ` - ${routeTitle}`;
    }
    document.title = title;
  }

  // WATCHERS
  watch(router.currentRoute, () => {
    updateDocumentTitle();
  });

  return {
    // STATE
    userNotification,
    loader,
    version,
    versionLoading,

    // GETTERS
    // rootUrl,
    apiUrl,

    // ACTIONS
    fetchVersion,
    showSuccessToast,
    showWarningToast,
    showInfoToast,
    showErrorToast,
  };
});

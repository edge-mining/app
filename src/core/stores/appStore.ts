import { defineStore } from "pinia";
import { computed, ref, watch } from "vue";
import router from "../../router";
import { useLoader } from "../composables/useLoader";
import type { UserNotification } from "../models/userNotification";
import type { AppVersion } from "../models/appVersion";

export const useAppStore = defineStore("app", () => {
  // STATE
  const userNotification = ref<UserNotification>();
  const coreVersion = ref<string>("");
  const coreName = ref<string>("Edge Mining");
  const frontendVersion = __APP_VERSION__;
  const appVersion = ref<AppVersion>({
    version: "",
    buildDate: "",
    commit: "",
  });
  const appVersionLoading = ref(true);
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
    // userNotification.value = {
    //   status,
    //   message: msg,
    // };
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

  async function fetchCoreVersion() {
    try {
      const response = await fetch(`${rootUrl.value}/version/core`);
      if (response.ok) {
        const data = await response.json();
        coreVersion.value = data.version;
        coreName.value = data.name;
        updateDocumentTitle();
      }
    } catch (error) {
      console.error("Failed to fetch core version:", error);
    }
  }

  async function fetchAppVersion() {
    appVersionLoading.value = true;
    try {
      const response = await fetch(`${rootUrl.value}/version/app`);
      if (response.ok) {
        appVersion.value = await response.json();
      }
    } catch (error) {
      console.warn("Failed to fetch app version:", error);
    } finally {
      appVersionLoading.value = false;
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
    coreVersion,
    coreName,
    frontendVersion,
    appVersion,
    appVersionLoading,

    // GETTERS
    // rootUrl,
    apiUrl,

    // ACTIONS
    fetchCoreVersion,
    fetchAppVersion,
    showSuccessToast,
    showWarningToast,
    showInfoToast,
    showErrorToast,
  };
});

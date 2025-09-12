import { defineStore } from "pinia";
import { computed, ref, watch } from "vue";
import router from "../../router";
import { useLoader } from "../composables/useLoader";
import type { UserNotification } from "../models/userNotification";

export const useAppStore = defineStore("app", () => {
  // STATE
  const userNotification = ref<UserNotification>();
  // The state bound to the loader shown in the App.vue component. Can be used by any component or service that needs to put
  // the user on hold.
  const loader = useLoader();

  // GETTERS
  const rootUrl = computed(() => "http://localhost:8001"); // Hardcoded for now, should be configurable
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

  // WATCHERS
  watch(router.currentRoute, () => {
    let title = "Edge Mining";
    const routeTitle = router.currentRoute.value.meta?.title;
    if (routeTitle) {
      title += ` - ${routeTitle}`;
    }
    document.title = title;
  });

  return {
    // STATE
    userNotification,
    loader,

    // GETTERS
    // rootUrl,
    apiUrl,

    // ACTIONS
    showSuccessToast,
    showWarningToast,
    showInfoToast,
    showErrorToast,
  };
});

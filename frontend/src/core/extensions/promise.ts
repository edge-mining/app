import { type AxiosResponse } from "axios";
import { useAppStore } from "../stores/appStore";

/**
 * The following lines extend the browser native Promise class to enhance the handling of the
 * spinloader AKA busy indicator or the display of error messages
 */
declare global {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  interface Promise<T> {
    addLoadSpinner<T>(this: Promise<T>): Promise<T>;
    getData<T>(this: Promise<AxiosResponse<T>>): Promise<T>;
    catchErrorWithToast<T>(this: Promise<T>): Promise<void | T>;
    showToasts<T>(
      this: Promise<T>,
      successMsg: string,
      errorMsg: string
    ): Promise<void | T>;
  }
}

/**
 * As soon as this method is invoked, it retrieves the appStore to show the spinloader and
 * hides it when the promise is completed
 */
Promise.prototype.addLoadSpinner = function <T>(this: Promise<T>): Promise<T> {
  const appStore = useAppStore();
  const promise = this;
  appStore.loader.show();
  return promise.finally(() => appStore.loader.hide());
};

/**
 * Extrapolates the data property out of the axios calls to make them less redundant
 */
Promise.prototype.getData = function <T>(
  this: Promise<AxiosResponse<T>>
): Promise<T> {
  return this.then((res) => res.data);
};

/**
 * Called on an Promise, registers a catch callback that tries to get infos from the
 * given parameter and displays it as a toast notification
 */
Promise.prototype.catchErrorWithToast = function <T>(
  this: Promise<T>
): Promise<void | T> {
  const appStore = useAppStore();
  return this.catch((err) => {
    let message = "Unknown error";
    if (err?.response?.data) {
      message = err.response.data;
    } else if (err?.message) {
      message = err.message;
    }
    appStore.showErrorToast(message);
  });
};

/**
 * Called on an Promise, registers a then and  catch callback.
 * The first one will show a success Toast Notification upon completion.
 * The latter will show an error Toast Notification upon failure.
 */
Promise.prototype.showToasts = function <T>(
  this: Promise<T>,
  successMsg: string,
  errorMsg: string
): Promise<void | T> {
  const appStore = useAppStore();

  return this.then(() => {
    appStore.showSuccessToast(successMsg);
  }).catch((err) => {
    appStore.showErrorToast(errorMsg, err);
  });
};

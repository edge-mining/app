import axios, { type AxiosRequestConfig, type AxiosResponse } from "axios";
import { useAppStore } from "../stores/appStore";
import * as PromiseExtensions from "../extensions/promise";

/**
 * Base service class, wraps common http methods for all services.
 * The inheriting services should not use axios call directly.
 */
export class BaseService {
  appStore = useAppStore();

  get<T>(url: string, request?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return axios.get<T>(this.appStore.apiUrl + url, request);
  }

  post<T>(
    url: string,
    data: any,
    request?: AxiosRequestConfig
  ): Promise<AxiosResponse<T>> {
    return axios.post<T>(this.appStore.apiUrl + url, data, request);
  }

  delete<T>(
    url: string,
    request?: AxiosRequestConfig
  ): Promise<AxiosResponse<T>> {
    return axios.delete<T>(this.appStore.apiUrl + url, request);
  }
}

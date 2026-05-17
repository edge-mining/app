import { BaseService } from "./baseService";
import type { Notifier, ConfigSchema, TestNotifierResult } from "../models/notifier";

export class NotifierService extends BaseService {
  getNotifiers(): Promise<Notifier[]> {
    return this.get<Notifier[]>("/notifiers").getData();
  }

  getNotifier(notifierId: string): Promise<Notifier> {
    return this.get<Notifier>(`/notifiers/${notifierId}`).getData();
  }

  addNotifier(notifier: Notifier): Promise<Notifier> {
    return this.post<Notifier>("/notifiers", notifier).getData();
  }

  updateNotifier(notifierId: string, notifier: Partial<Notifier>): Promise<Notifier> {
    return this.put<Notifier>(`/notifiers/${notifierId}`, notifier).getData();
  }

  deleteNotifier(notifierId: string): Promise<Notifier> {
    return this.delete<Notifier>(`/notifiers/${notifierId}`).getData();
  }

  getAdapterTypes(): Promise<string[]> {
    return this.get<string[]>("/notifiers/types").getData();
  }

  getConfigSchema(adapterType: string): Promise<ConfigSchema> {
    return this.get<ConfigSchema>(`/notifiers/types/${adapterType}/config-schema`).getData();
  }

  testNotifier(notifierId: string): Promise<TestNotifierResult> {
    return this.post<TestNotifierResult>(`/notifiers/${notifierId}/test`, {}).getData();
  }

  getExternalServices(adapterType: string): Promise<string | null> {
    return this.get<string | null>(`/notifiers/types/${adapterType}/external-services`).getData();
  }
}

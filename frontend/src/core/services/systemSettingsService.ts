import { BaseService } from "./baseService";
import type { SystemConfiguration } from "../models/systemConfiguration";

export class SystemSettingsService extends BaseService {
  getSystemConfiguration(): Promise<SystemConfiguration> {
    return this.get<SystemConfiguration>("/system/settings").getData();
  }

  updateSystemConfiguration(
    configuration: SystemConfiguration
  ): Promise<SystemConfiguration> {
    return this.put<SystemConfiguration>("/system/settings", configuration).getData();
  }
}

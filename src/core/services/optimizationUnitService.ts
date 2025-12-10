import { BaseService } from "./baseService";
import type { OptimizationUnit, OptimizationUnitCreate, OptimizationUnitUpdate } from "../models/optimizationUnit";

export class OptimizationUnitService extends BaseService {
  // Basic CRUD operations
  getOptimizationUnits(): Promise<OptimizationUnit[]> {
    return this.get<OptimizationUnit[]>("/optimization-units").getData();
  }

  getOptimizationUnit(unitId: string): Promise<OptimizationUnit> {
    return this.get<OptimizationUnit>(`/optimization-units/${unitId}`).getData();
  }

  addOptimizationUnit(unit: OptimizationUnitCreate): Promise<OptimizationUnit> {
    return this.post<OptimizationUnit>("/optimization-units", unit).getData();
  }

  updateOptimizationUnit(unitId: string, unit: OptimizationUnitUpdate): Promise<OptimizationUnit> {
    return this.put<OptimizationUnit>(`/optimization-units/${unitId}`, unit).getData();
  }

  deleteOptimizationUnit(unitId: string): Promise<OptimizationUnit> {
    return this.delete<OptimizationUnit>(`/optimization-units/${unitId}`).getData();
  }

  // Enable/Disable operations
  enableOptimizationUnit(unitId: string): Promise<OptimizationUnit> {
    return this.post<OptimizationUnit>(`/optimization-units/${unitId}/enable`, {}).getData();
  }

  disableOptimizationUnit(unitId: string): Promise<OptimizationUnit> {
    return this.post<OptimizationUnit>(`/optimization-units/${unitId}/disable`, {}).getData();
  }

  // Assignment operations
  assignEnergySource(unitId: string, energySourceId: string): Promise<OptimizationUnit> {
    return this.post<OptimizationUnit>(`/optimization-units/${unitId}/energy-source?energy_source_id=${energySourceId}`, {}).getData();
  }

  assignPolicy(unitId: string, policyId: string): Promise<OptimizationUnit> {
    return this.post<OptimizationUnit>(`/optimization-units/${unitId}/policy?policy_id=${policyId}`, {}).getData();
  }

  // Miner operations
  assignMiners(unitId: string, minerIds: string[]): Promise<OptimizationUnit> {
    return this.post<OptimizationUnit>(`/optimization-units/${unitId}/miners`, minerIds).getData();
  }

  addMiner(unitId: string, minerId: string): Promise<OptimizationUnit> {
    return this.post<OptimizationUnit>(`/optimization-units/${unitId}/miners/single?miner_id=${minerId}`, {}).getData();
  }

  removeMiner(unitId: string, minerId: string): Promise<OptimizationUnit> {
    return this.delete<OptimizationUnit>(`/optimization-units/${unitId}/miners/${minerId}`).getData();
  }

  // Notifier operations
  assignNotifiers(unitId: string, notifierIds: string[]): Promise<OptimizationUnit> {
    return this.post<OptimizationUnit>(`/optimization-units/${unitId}/notifiers`, notifierIds).getData();
  }

  addNotifier(unitId: string, notifierId: string): Promise<OptimizationUnit> {
    return this.post<OptimizationUnit>(`/optimization-units/${unitId}/notifiers/single?notifier_id=${notifierId}`, {}).getData();
  }

  removeNotifier(unitId: string, notifierId: string): Promise<OptimizationUnit> {
    return this.delete<OptimizationUnit>(`/optimization-units/${unitId}/notifiers/${notifierId}`).getData();
  }
}

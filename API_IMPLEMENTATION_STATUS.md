# Edge Mining API Implementation Status

This document lists all the FastAPI endpoints exposed by the backend and tracks their implementation status in the frontend.

## API Base URL
All endpoints are prefixed with the API base URL (typically `/api` or similar).

---

## 1. Energy Sources API (`/energy-sources`)

### Endpoints:

| Method | Endpoint | Description | Frontend Service | Frontend Page | Status |
|--------|----------|-------------|------------------|---------------|---------|
| GET | `/energy-sources` | Get list of all energy sources | `EnergySourceService.getEnergySources()` | `EnergySourcesSettingsView.vue` | ✅ Implemented |
| POST | `/energy-sources` | Create a new energy source | `EnergySourceService.addEnergySource()` | `EnergySourcesSettingsView.vue` | ✅ Implemented |
| GET | `/energy-sources/types` | Get available energy source types | `EnergySourceService.getEnergySourceTypes()` | - | ✅ Implemented |
| GET | `/energy-sources/{source_id}` | Get specific energy source details | `EnergySourceService.getEnergySource()` | - | ✅ Implemented |
| PUT | `/energy-sources/{source_id}` | Update an energy source | `EnergySourceService.updateEnergySource()` | - | ✅ Implemented |
| DELETE | `/energy-sources/{source_id}` | Delete an energy source | `EnergySourceService.deleteEnergySource()` | - | ✅ Implemented |

**Location in backend:** `core/edge_mining/adapters/domain/energy/fast_api/router.py`

---

## 2. Energy Monitors API (`/energy-monitors`)

### Endpoints:

| Method | Endpoint | Description | Frontend Service | Frontend Page | Status |
|--------|----------|-------------|------------------|---------------|---------|
| GET | `/energy-monitors` | Get list of all energy monitors | `EnergyMonitorService.getEnergyMonitors()` | `EnergyMonitorSettingsView.vue` | ✅ Implemented |
| POST | `/energy-monitors` | Create a new energy monitor | `EnergyMonitorService.addEnergyMonitor()` | `EnergyMonitorSettingsView.vue` | ✅ Implemented |
| GET | `/energy-monitors/types` | Get available energy monitor types | `EnergyMonitorService.getAdapterTypes()` | `EnergyMonitorSettingsView.vue` | ✅ Implemented |
| GET | `/energy-monitors/types/{adapter_type}/config-schema` | Get config schema for monitor type | `EnergyMonitorService.getConfigSchema()` | `EnergyMonitorSettingsView.vue` | ✅ Implemented |
| GET | `/energy-monitors/{monitor_id}` | Get specific energy monitor | `EnergyMonitorService.getEnergyMonitor()` | - | ✅ Implemented |
| PUT | `/energy-monitors/{monitor_id}` | Update an energy monitor | `EnergyMonitorService.updateEnergyMonitor()` | - | ✅ Implemented |
| DELETE | `/energy-monitors/{monitor_id}` | Delete an energy monitor | `EnergyMonitorService.deleteEnergyMonitor()` | - | ✅ Implemented |

**Location in backend:** `core/edge_mining/adapters/domain/energy/fast_api/router.py`

---

## 3. Miners API (`/miners`)

### Endpoints:

| Method | Endpoint | Description | Frontend Service | Frontend Page | Status |
|--------|----------|-------------|------------------|---------------|---------|
| GET | `/miners` | Get list of all miners | `MinerService.getMiners()` | `MinersSettingsView.vue` | ✅ Implemented |
| POST | `/miners` | Create a new miner | `MinerService.addMiner()` | `MinersSettingsView.vue` | ✅ Implemented |
| GET | `/miners/{miner_id}` | Get specific miner details | `MinerService.getMiner()` | - | ✅ Implemented |
| PUT | `/miners/{miner_id}` | Update a miner | `MinerService.updateMiner()` | - | ✅ Implemented |
| DELETE | `/miners/{miner_id}` | Delete a miner | `MinerService.deleteMiner()` | - | ✅ Implemented |
| POST | `/miners/{miner_id}/start` | Start a miner | `MinerService.startMiner()` | - | ✅ Implemented |
| POST | `/miners/{miner_id}/stop` | Stop a miner | `MinerService.stopMiner()` | - | ✅ Implemented |
| GET | `/miners/{miner_id}/status` | Get miner status | `MinerService.getMinerStatus()` | - | ✅ Implemented |
| POST | `/miners/{miner_id}/activate` | Activate a miner | `MinerService.activateMiner()` | - | ✅ Implemented |
| POST | `/miners/{miner_id}/deactivate` | Deactivate a miner | `MinerService.deactivateMiner()` | - | ✅ Implemented |
| POST | `/miners/{miner_id}/set-controller` | Set miner controller | `MinerService.setMinerController()` | - | ✅ Implemented |

**Location in backend:** `core/edge_mining/adapters/domain/miner/fast_api/router.py`

---

## 4. Miner Controllers API (`/miner-controllers`)

### Endpoints:

| Method | Endpoint | Description | Frontend Service | Frontend Page | Status |
|--------|----------|-------------|------------------|---------------|---------|
| GET | `/miner-controllers` | Get list of all miner controllers | `MinerControllerService.getMinerControllers()` | `MinerControllersSettingsView.vue` | ✅ Implemented |
| POST | `/miner-controllers` | Create a new miner controller | `MinerControllerService.addMinerController()` | `MinerControllersSettingsView.vue` | ✅ Implemented |
| GET | `/miner-controllers/types` | Get available controller types | `MinerControllerService.getAdapterTypes()` | `MinerControllersSettingsView.vue` | ✅ Implemented |
| GET | `/miner-controllers/types/{adapter_type}/config-schema` | Get config schema for controller type | `MinerControllerService.getConfigSchema()` | `MinerControllersSettingsView.vue` | ✅ Implemented |
| GET | `/miner-controllers/{controller_id}` | Get specific controller | `MinerControllerService.getMinerController()` | - | ✅ Implemented |
| PUT | `/miner-controllers/{controller_id}` | Update a controller | `MinerControllerService.updateMinerController()` | `MinerControllersSettingsView.vue` | ✅ Implemented |
| DELETE | `/miner-controllers/{controller_id}` | Delete a controller | `MinerControllerService.deleteMinerController()` | `MinerControllersSettingsView.vue` | ✅ Implemented |

**Location in backend:** `core/edge_mining/adapters/domain/miner/fast_api/router.py`

---

## 5. Policies API (`/policies`)

### Endpoints:

| Method | Endpoint | Description | Frontend Service | Frontend Page | Status |
|--------|----------|-------------|------------------|---------------|---------|
| GET | `/policies` | Get list of all optimization policies | `PolicyService.getPolicies()` | `PoliciesSettingsView.vue` | ✅ Implemented |
| POST | `/policies` | Create a new policy | `PolicyService.addPolicy()` | `PoliciesSettingsView.vue` | ✅ Implemented |
| GET | `/policies/{policy_id}` | Get specific policy | `PolicyService.getPolicy()` | `PoliciesSettingsView.vue` | ✅ Implemented |
| PUT | `/policies/{policy_id}` | Update a policy | `PolicyService.updatePolicy()` | `PoliciesSettingsView.vue` | ✅ Implemented |
| DELETE | `/policies/{policy_id}` | Delete a policy | `PolicyService.deletePolicy()` | `PoliciesSettingsView.vue` | ✅ Implemented |
| GET | `/policies/{policy_id}/check` | Check if policy is valid | `PolicyService.checkPolicy()` | `PoliciesSettingsView.vue` | ✅ Implemented |

**Location in backend:** `core/edge_mining/adapters/domain/policy/fast_api/router.py`

---

## 6. Policy Rules API (`/policies/{policy_id}/rules`)

### Endpoints:

| Method | Endpoint | Description | Frontend Service | Frontend Page | Status |
|--------|----------|-------------|------------------|---------------|---------|
| POST | `/policies/{policy_id}/rules` | Add rule to policy | `PolicyService.addRule()` | `PoliciesSettingsView.vue` | ✅ Implemented |
| GET | `/policies/{policy_id}/types/{rule_type}` | Get rules by type | `PolicyService.getRulesByType()` | - | ✅ Implemented |
| GET | `/policies/{policy_id}/rules/{rule_id}` | Get specific rule | `PolicyService.getRule()` | - | ✅ Implemented |
| PUT | `/policies/{policy_id}/rules/{rule_id}` | Update a rule | `PolicyService.updateRule()` | `PoliciesSettingsView.vue` | ✅ Implemented |
| DELETE | `/policies/{policy_id}/rules/{rule_id}` | Delete a rule | `PolicyService.deleteRule()` | `PoliciesSettingsView.vue` | ✅ Implemented |
| GET | `/policies/{policy_id}/rules/{rule_id}/enable` | Enable a rule | `PolicyService.enableRule()` | `PoliciesSettingsView.vue` | ✅ Implemented |
| GET | `/policies/{policy_id}/rules/{rule_id}/disable` | Disable a rule | `PolicyService.disableRule()` | `PoliciesSettingsView.vue` | ✅ Implemented |

**Location in backend:** `core/edge_mining/adapters/domain/policy/fast_api/router.py`

---

## 7. Forecast Providers API (`/forecast-providers`)

### Endpoints:

| Method | Endpoint | Description | Frontend Service | Frontend Page | Status |
|--------|----------|-------------|------------------|---------------|---------|
| GET | `/forecast-providers` | Get list of all forecast providers | `ForecastProviderService.getForecastProviders()` | `ForecastProvidersSettingsView.vue` | ✅ Implemented |
| POST | `/forecast-providers` | Create a new forecast provider | `ForecastProviderService.addForecastProvider()` | `ForecastProvidersSettingsView.vue` | ✅ Implemented |
| GET | `/forecast-providers/types` | Get available provider types | `ForecastProviderService.getAdapterTypes()` | `ForecastProvidersSettingsView.vue` | ✅ Implemented |
| GET | `/forecast-providers/types/{adapter_type}/config-schema` | Get config schema for provider type | `ForecastProviderService.getConfigSchema()` | `ForecastProvidersSettingsView.vue` | ✅ Implemented |
| GET | `/forecast-providers/{provider_id}` | Get specific provider | `ForecastProviderService.getForecastProvider()` | - | ✅ Implemented |
| PUT | `/forecast-providers/{provider_id}` | Update a provider | `ForecastProviderService.updateForecastProvider()` | `ForecastProvidersSettingsView.vue` | ✅ Implemented |
| DELETE | `/forecast-providers/{provider_id}` | Delete a provider | `ForecastProviderService.deleteForecastProvider()` | `ForecastProvidersSettingsView.vue` | ✅ Implemented |

**Location in backend:** `core/edge_mining/adapters/domain/forecast/fast_api/router.py`

---

## 8. Notifiers API (`/notifiers`)

### Endpoints:

| Method | Endpoint | Description | Frontend Service | Frontend Page | Status |
|--------|----------|-------------|------------------|---------------|---------|
| GET | `/notifiers` | Get list of all notifiers | `NotifierService.getNotifiers()` | `NotifiersSettingsView.vue` | ✅ Implemented |
| POST | `/notifiers` | Create a new notifier | `NotifierService.addNotifier()` | `NotifiersSettingsView.vue` | ✅ Implemented |
| GET | `/notifiers/types` | Get available notifier types | `NotifierService.getAdapterTypes()` | `NotifiersSettingsView.vue` | ✅ Implemented |
| GET | `/notifiers/types/{adapter_type}/config-schema` | Get config schema for notifier type | `NotifierService.getConfigSchema()` | `NotifiersSettingsView.vue` | ✅ Implemented |
| GET | `/notifiers/{notifier_id}` | Get specific notifier | `NotifierService.getNotifier()` | - | ✅ Implemented |
| PUT | `/notifiers/{notifier_id}` | Update a notifier | `NotifierService.updateNotifier()` | `NotifiersSettingsView.vue` | ✅ Implemented |
| DELETE | `/notifiers/{notifier_id}` | Delete a notifier | `NotifierService.deleteNotifier()` | `NotifiersSettingsView.vue` | ✅ Implemented |
| POST | `/notifiers/{notifier_id}/test` | Test a notifier | `NotifierService.testNotifier()` | `NotifiersSettingsView.vue` | ✅ Implemented |

**Location in backend:** `core/edge_mining/adapters/domain/notification/fast_api/router.py`

---

## 9. External Services API (`/external-services`)

### Endpoints:

| Method | Endpoint | Description | Frontend Service | Frontend Page | Status |
|--------|----------|-------------|------------------|---------------|---------|
| GET | `/external-services` | Get list of all external services | `ExternalServiceService.getExternalServices()` | `ExternalServicesSettingsView.vue` | ✅ Implemented |
| POST | `/external-services` | Create a new external service | `ExternalServiceService.addExternalService()` | `ExternalServicesSettingsView.vue` | ✅ Implemented |
| GET | `/external-services/types` | Get available service types | `ExternalServiceService.getAdapterTypes()` | `ExternalServicesSettingsView.vue` | ✅ Implemented |
| GET | `/external-services/types/{adapter_type}/config-schema` | Get config schema for service type | `ExternalServiceService.getConfigSchema()` | `ExternalServicesSettingsView.vue` | ✅ Implemented |
| GET | `/external-services/{service_id}` | Get specific service | `ExternalServiceService.getExternalService()` | - | ✅ Implemented |
| PUT | `/external-services/{service_id}` | Update a service | `ExternalServiceService.updateExternalService()` | `ExternalServicesSettingsView.vue` | ✅ Implemented |
| DELETE | `/external-services/{service_id}` | Delete a service | `ExternalServiceService.deleteExternalService()` | `ExternalServicesSettingsView.vue` | ✅ Implemented |

**Location in backend:** `core/edge_mining/adapters/infrastructure/external_services/fast_api/router.py`

---

## 10. Rule Engine API (`/rule-engine`)

### Endpoints:

| Method | Endpoint | Description | Frontend Service | Frontend Page | Status |
|--------|----------|-------------|------------------|---------------|---------|
| GET | `/rule-engine/config` | Get rule engine configuration | `RuleEngineService.getConfig()` | - | ✅ Implemented |
| GET | `/rule-engine/info` | Get rule engine capabilities info | `RuleEngineService.getInfo()` | - | ✅ Implemented |
| POST | `/rule-engine/evaluate` | Evaluate rules against context | `RuleEngineService.evaluate()` | - | ✅ Implemented |
| POST | `/rule-engine/validate` | Validate rule conditions | `RuleEngineService.validate()` | - | ✅ Implemented |

**Location in backend:** `core/edge_mining/adapters/infrastructure/rule_engine/fast_api/router.py`

---

## Summary Statistics

### By Domain:

- **Energy Sources**: 6/6 endpoints implemented (100%) ✅ **PHASE 1 COMPLETE**
- **Energy Monitors**: 7/7 endpoints implemented (100%) ✅ **PHASE 1 COMPLETE**
- **Miners**: 11/11 endpoints implemented (100%) ✅ **PHASE 1 COMPLETE**
- **Miner Controllers**: 7/7 endpoints implemented (100%) ✅ **PHASE 2 COMPLETE**
- **Policies**: 6/6 endpoints implemented (100%) ✅ **PHASE 3 COMPLETE**
- **Policy Rules**: 7/7 endpoints implemented (100%) ✅ **PHASE 3 COMPLETE**
- **Forecast Providers**: 7/7 endpoints implemented (100%) ✅ **PHASE 4 COMPLETE**
- **Notifiers**: 8/8 endpoints implemented (100%) ✅ **PHASE 5 COMPLETE**
- **External Services**: 7/7 endpoints implemented (100%) ✅ **PHASE 6 COMPLETE**
- **Rule Engine**: 4/4 endpoints implemented (100%) ✅ **COMPLETE**

### Overall Progress:
- **Total Endpoints**: 70
- **Implemented**: 70 (100%) ✅ **ALL COMPLETE**
- **To Implement**: 0 (0%)

---

## Existing Frontend Implementation

### Services (in `src/core/services/`):
1. ✅ `MinerService.ts` - **COMPLETE** - Full CRUD + control operations (11/11 endpoints)
2. ✅ `EnergySourceService.ts` - **COMPLETE** - Full CRUD + types (6/6 endpoints)
3. ✅ `EnergyMonitorService.ts` - **COMPLETE** - Full CRUD + types + config schema (7/7 endpoints)
4. ✅ `MinerControllerService.ts` - **COMPLETE** - Full CRUD + types + config schema (7/7 endpoints)
5. ✅ `ForecastProviderService.ts` - **COMPLETE** - Full CRUD + types + config schema (7/7 endpoints)
6. ✅ `PolicyService.ts` - **COMPLETE** - Full CRUD + rules management + check (13/13 endpoints)
7. ✅ `NotifierService.ts` - **COMPLETE** - Full CRUD + types + config schema + test (8/8 endpoints)
8. ✅ `ExternalServiceService.ts` - **COMPLETE** - Full CRUD + types + config schema (7/7 endpoints)
9. ✅ `RuleEngineService.ts` - **COMPLETE** - Config, info, evaluate, validate (4/4 endpoints)
10. ✅ `BaseService.ts` - Base HTTP service class with GET, POST, PUT, DELETE methods

### Views/Pages (in `src/views/`):
1. ✅ `DashboardView.vue` - Main dashboard
2. ✅ `settings/MinersSettingsView.vue` - **UPDATED** - Full CRUD + control operations (start/stop/activate/deactivate)
3. ✅ `settings/EnergySourcesSettingsView.vue` - **UPDATED** - Full CRUD operations (create, read, update, delete)
4. ✅ `settings/EnergyMonitorSettingsView.vue` - **UPDATED** - Full CRUD operations with modal edit support
5. ✅ `settings/MinerControllersSettingsView.vue` - **NEW** - Full CRUD operations with modal edit support
6. ✅ `settings/ForecastProvidersSettingsView.vue` - **NEW** - Full CRUD operations with modal edit support
7. ✅ `settings/PoliciesSettingsView.vue` - **NEW** - Full CRUD operations with rules management modal
8. ✅ `settings/NotifiersSettingsView.vue` - **NEW** - Full CRUD operations with test notification feature
9. ✅ `settings/ExternalServicesSettingsView.vue` - **NEW** - Full CRUD operations with modal edit support

### Components (in `src/components/`):
1. ✅ `miners/MinerRow.vue` - **UPDATED** - Display miner row with edit/delete/control buttons
2. ✅ `miners/MinerRowEdit.vue` - Edit miner row inline
3. ✅ `energySources/EnergySourceRow.vue` - **UPDATED** - Display energy source row with edit/delete buttons
4. ✅ `energySources/EnergySourceRowEdit.vue` - Edit energy source row inline
5. ✅ `energyMonitors/EnergyMonitorRow.vue` - **UPDATED** - Display energy monitor row with edit/delete buttons
6. ✅ `energyMonitors/EnergyMonitorRowEdit.vue` - Edit energy monitor row (used in modal)
7. ✅ `energyMonitors/EnergyMonitorConfigForm.vue` - Energy monitor config form
8. ✅ `minerControllers/MinerControllerRow.vue` - **NEW** - Display miner controller row with edit/delete buttons
9. ✅ `minerControllers/MinerControllerConfigForm.vue` - **NEW** - Miner controller config form
10. ✅ `forecastProviders/ForecastProviderRow.vue` - **NEW** - Display forecast provider row with edit/delete buttons
11. ✅ `forecastProviders/ForecastProviderConfigForm.vue` - **NEW** - Forecast provider config form
12. ✅ `policies/PolicyRow.vue` - **NEW** - Display policy row with edit/delete/rules/check buttons
13. ✅ `policies/PolicyRuleRow.vue` - **NEW** - Display policy rule row with edit/delete/toggle enabled
14. ✅ `notifiers/NotifierRow.vue` - **NEW** - Display notifier row with edit/delete/test buttons
15. ✅ `notifiers/NotifierConfigForm.vue` - **NEW** - Notifier config form with dynamic schema
16. ✅ `externalServices/ExternalServiceRow.vue` - **NEW** - Display external service row with edit/delete buttons
17. ✅ `externalServices/ExternalServiceConfigForm.vue` - **NEW** - External service config form with dynamic schema

---

## Priority Implementation Plan

### Phase 1: Complete CRUD for Existing Entities ✅ **COMPLETED**

**Backend Services (All endpoints implemented):**
1. ✅ Complete Miners CRUD operations (update, delete, get by ID)
2. ✅ Complete Energy Sources CRUD operations (update, delete, get by ID)
3. ✅ Complete Energy Monitors CRUD operations (update, delete, get by ID)
4. ✅ Add miner control operations (start/stop/activate/deactivate)
5. ✅ Add BaseService PUT method
6. ✅ Add Energy Source types endpoint
7. ✅ Energy Monitor types and config schema endpoints were already implemented

**Frontend UI (All CRUD operations functional):**
8. ✅ Add edit/delete buttons to MinerRow component with miner control buttons
9. ✅ Add edit/delete handlers to MinersSettingsView with inline editing
10. ✅ Update MinerStore with all CRUD and control operations
11. ✅ Add edit/delete buttons to EnergySourceRow component
12. ✅ Add edit/delete handlers to EnergySourcesSettingsView with inline editing
13. ✅ Update EnergySourceStore with update and delete operations
14. ✅ Add edit/delete buttons to EnergyMonitorRow component
15. ✅ Add edit/delete handlers to EnergyMonitorSettingsView with modal editing
16. ✅ Update EnergyMonitorStore with update and delete operations

### Phase 2: Miner Controllers ✅ **COMPLETED**
1. ✅ Create MinerControllerService
2. ✅ Create MinerController views and components
3. ✅ Implement all CRUD operations

### Phase 3: Policies and Rules ✅ **COMPLETED**
1. ✅ Create PolicyService
2. ✅ Create Policy views and components
3. ✅ Implement rule management UI
4. ✅ Integrate with Rule Engine validation API (via checkPolicy endpoint)

### Phase 4: Forecast Providers ✅ **COMPLETED**
1. ✅ Create ForecastProviderService
2. ✅ Create ForecastProvider views and components
3. ✅ Implement all CRUD operations

### Phase 5: Notifiers ✅ **COMPLETED**
1. ✅ Create NotifierService
2. ✅ Create Notifier views and components
3. ✅ Implement all CRUD operations
4. ✅ Add test notification feature

### Phase 6: External Services ✅ **COMPLETED**
1. ✅ Create ExternalServiceService
2. ✅ Create ExternalService views and components
3. ✅ Implement all CRUD operations

### Phase 7: Optimization Units (Not yet discovered in API)
- Need to check if optimization units have API endpoints

---

## Notes

- All services should extend `BaseService` class
- Follow the existing pattern for service methods
- Use TypeScript interfaces/types from `src/core/models/` directory
- Ensure proper error handling and loading states
- Add proper TypeScript types for all API responses
- Consider adding Vuex/Pinia stores for state management where appropriate

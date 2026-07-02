# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- **Home load history timezone handling**: the optimization loop built its 24h look-back window with a naive `datetime.now()`, clashing with the timezone-aware (UTC) timestamps returned by Home Assistant and the persistence layer and raising "can't compare offset-naive and offset-aware datetimes". The look-back window, the merged-consumption timestamp and the history purge cut-off now use UTC-aware timestamps consistently (`optimization_service.py`, `home_load_history_service.py`).
- Unified the dashboard background color with the rest of the interface: the main content area now uses the same grey (`base-100`) as the sidebar, cards, top bar, and bottom bar instead of a lighter `base-200`, reinforcing the flat visual style (#32).

### Added

- Global Home Assistant connection status indicator in the bottom bar, always visible: green when connected, red when disconnected or not configured. Clicking it opens a popover with the per-service status detail and a button to jump straight to the Home Assistant settings (the External Services page lands pre-filtered on the relevant adapter) (#20).
- Unit-of-measure fields in configuration forms are now selected through a segmented control (e.g. `W` / `kW` / `MW`, `Wh` / `kWh` / `MWh`, `GH/s` / `TH/s` / `PH/s`) instead of a free-text input, preventing inconsistent or invalid values. The available options are inferred automatically from each field, so the control applies to every configuration form (#18).
- Home Assistant entity fields now show a selectable entity-domain prefix (e.g. `sensor.`, `switch.`) as a dropdown next to the input, so the user only types the entity object id. The domain defaults to the one derived from the field's value/default/name and can be overridden, with the prefix now enabled on Forecast Provider and Miner Controller forms too (handling controllers that mix `switch.` and `sensor.` entities) (#39).
- **Additive history backfill on manual collection**: a manual per-device collection now re-fetches the whole requested look-back window from the provider and merges it into the store (de-duplicated by the `(device_id, timestamp)` primary key), filling internal gaps without dropping existing data. Previously it only ingested incrementally from the last stored point, ignoring `lookback_hours`. `EnergyLoadHistoryProviderPort.get_power_points` gains a `force_refresh` flag; the scheduled collection stays incremental (`ports.py`, `home_assistant_api_history.py`, `home_load_history_service.py`).
- **Forecast retrain after manual collection**: the device history modal prompts the user to retrain the device's forecast model with the freshly collected data, triggering per-device training and refreshing the forecast on success (frontend).
- **Training outcome reporting** (`LoadTrainingResult` value object in `domain/home_load/value_objects.py`): `train_device` now reports whether a model was actually `trained` (with best adapter, MAE and sample count), `skipped` (with reason, e.g. insufficient history) or `failed`. The `training/trigger` endpoint surfaces the outcome and the UI shows a status toast, instead of always reporting a generic "completed".
- **Miner controller connection test** (`edge_mining/adapters/domain/miner/`):
  - New `POST /miner-controllers/test-connection` endpoint that tests a (non-persisted) controller configuration and returns a reachability result (`MinerControllerTestConnectionSchema`)
  - `MinerActionService.test_miner_controller_connection()` builds a fresh, uncached adapter from the controller entity and verifies the device responds (status / hashrate / power / device info)
  - `AdapterService.build_miner_controller_adapter()` to instantiate an adapter from a controller entity without using or polluting the adapters cache
  - Frontend: "Test Connection" button in the miner controller form, shown only for the PyASIC adapter type, with inline success/error feedback (#46)
- Configure and order controller features directly in the miner creation form,
  before the miner is saved (#48):
  - New REST endpoint `GET /miner-controllers/{controller_id}/supported-features`
    returning the feature types a controller supports, without requiring a
    persisted miner (`MinerActionService.get_controller_supported_features`).
  - The "Add Miner" form now shows a controller's features as soon as it is
    selected (with the backend defaults: enabled, priority 50), so priority and
    enabled/disabled state can be set during creation.
  - On save, the chosen priority/enabled values are applied after the controllers
    are linked. This also works for controllers newly added to an existing miner,
    without requiring a second save.
  
### Changed

- Reorganized configuration forms for readability: each entity field is now paired with its unit of measure on the same row, and fields are grouped by domain (Power / Energy) when at least two domains are present, preserving the chronological order within each group. Applied generically to all schema-driven configuration forms (#17).
- Paired entity/unit fields now use a compact layout: the unit segmented control is rendered inline next to the entity input, so each row keeps a single label and helper text and stays aligned regardless of text length. Configuration modals were widened for more breathing room (#17).
- Miner controller add/edit form now uses the shared schema-driven configuration form, so Home Assistant controllers (e.g. generic socket) benefit from entity/unit pairing and the unit segmented controls like the other forms (#17, #18).
- Cleaned up sidebar header: removed the "Edge Mining" text label and the username placeholder, left-aligned the logo with the sidebar menu items, and refined the green glow to originate from the logo area (#33).

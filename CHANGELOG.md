# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- **Home load history timezone handling**: the optimization loop built its 24h look-back window with a naive `datetime.now()`, clashing with the timezone-aware (UTC) timestamps returned by Home Assistant and the persistence layer and raising "can't compare offset-naive and offset-aware datetimes". The look-back window, the merged-consumption timestamp and the history purge cut-off now use UTC-aware timestamps consistently (`optimization_service.py`, `home_load_history_service.py`).

### Added

- **Additive history backfill on manual collection**: a manual per-device collection now re-fetches the whole requested look-back window from the provider and merges it into the store (de-duplicated by the `(device_id, timestamp)` primary key), filling internal gaps without dropping existing data. Previously it only ingested incrementally from the last stored point, ignoring `lookback_hours`. `EnergyLoadHistoryProviderPort.get_power_points` gains a `force_refresh` flag; the scheduled collection stays incremental (`ports.py`, `home_assistant_api_history.py`, `home_load_history_service.py`).
- **Forecast retrain after manual collection**: the device history modal prompts the user to retrain the device's forecast model with the freshly collected data, triggering per-device training and refreshing the forecast on success (frontend).
- **Training outcome reporting** (`LoadTrainingResult` value object in `domain/home_load/value_objects.py`): `train_device` now reports whether a model was actually `trained` (with best adapter, MAE and sample count), `skipped` (with reason, e.g. insufficient history) or `failed`. The `training/trigger` endpoint surfaces the outcome and the UI shows a status toast, instead of always reporting a generic "completed".

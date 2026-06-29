# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Miner controller connection test** (`edge_mining/adapters/domain/miner/`):
  - New `POST /miner-controllers/test-connection` endpoint that tests a (non-persisted) controller configuration and returns a reachability result (`MinerControllerTestConnectionSchema`)
  - `MinerActionService.test_miner_controller_connection()` builds a fresh, uncached adapter from the controller entity and verifies the device responds (status / hashrate / power / device info)
  - `AdapterService.build_miner_controller_adapter()` to instantiate an adapter from a controller entity without using or polluting the adapters cache
  - Frontend: "Test Connection" button in the miner controller form, shown only for the PyASIC adapter type, with inline success/error feedback (#46)

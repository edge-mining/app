# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Fetch device data (max hash rate, max power and model/hostname) from the
  controller while creating a miner, without saving it first (#49):
  - New REST endpoints `GET /miner-controllers/{controller_id}/limits` and
    `GET /miner-controllers/{controller_id}/info`, backed by
    `MinerActionService.get_controller_limits` / `get_controller_info`, which
    query a controller directly via a temporary miner.
  - The "Add Miner" form now enables the "fetch from miner" buttons for Max Hash
    Rate, Max Power and Model when at least one controller is selected, trying
    the selected controllers until one provides the value.

### Changed

- `MinerActionService`: extracted shared `_read_miner_info` / `_read_miner_limits`
  helpers and a `_temp_miner_for_controller` builder, reused by the miner- and
  controller-level info/limits/details reads.

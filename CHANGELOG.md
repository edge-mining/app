# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

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

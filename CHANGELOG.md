# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Unit-of-measure fields in configuration forms are now selected through a segmented control (e.g. `W` / `kW` / `MW`, `Wh` / `kWh` / `MWh`, `GH/s` / `TH/s` / `PH/s`) instead of a free-text input, preventing inconsistent or invalid values. The available options are inferred automatically from each field, so the control applies to every configuration form (#18).

### Changed

- Reorganized configuration forms for readability: each entity field is now paired with its unit of measure on the same row, and fields are grouped by domain (Power / Energy) when at least two domains are present, preserving the chronological order within each group. Applied generically to all schema-driven configuration forms (#17).

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Unit-of-measure fields in configuration forms are now selected through a segmented control (e.g. `W` / `kW` / `MW`, `Wh` / `kWh` / `MWh`, `GH/s` / `TH/s` / `PH/s`) instead of a free-text input, preventing inconsistent or invalid values. The available options are inferred automatically from each field, so the control applies to every configuration form (#18).
- Home Assistant entity fields now show a selectable entity-domain prefix (e.g. `sensor.`, `switch.`) as a dropdown next to the input, so the user only types the entity object id. The domain defaults to the one derived from the field's value/default/name and can be overridden, with the prefix now enabled on Forecast Provider and Miner Controller forms too (handling controllers that mix `switch.` and `sensor.` entities) (#39).

### Changed

- Reorganized configuration forms for readability: each entity field is now paired with its unit of measure on the same row, and fields are grouped by domain (Power / Energy) when at least two domains are present, preserving the chronological order within each group. Applied generically to all schema-driven configuration forms (#17).
- Paired entity/unit fields now use a compact layout: the unit segmented control is rendered inline next to the entity input, so each row keeps a single label and helper text and stays aligned regardless of text length. Configuration modals were widened for more breathing room (#17).
- Miner controller add/edit form now uses the shared schema-driven configuration form, so Home Assistant controllers (e.g. generic socket) benefit from entity/unit pairing and the unit segmented controls like the other forms (#17, #18).
- Cleaned up sidebar header: removed the "Edge Mining" text label and the username placeholder, left-aligned the logo with the sidebar menu items, and refined the green glow to originate from the logo area (#33).

### Fixed

- Unified the dashboard background color with the rest of the interface: the main content area now uses the same grey (`base-100`) as the sidebar, cards, top bar, and bottom bar instead of a lighter `base-200`, reinforcing the flat visual style (#32).

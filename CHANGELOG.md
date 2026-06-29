# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Heat Management (Climate domain)** — manage heat as a primary asset, driving mining to keep a space at a target temperature (#44):
  - `ClimateZone` (room/area to heat) and `ClimateMonitor` (temperature sensor) with daily temperature schedule, hysteresis and default target
  - Climate monitor adapters: Home Assistant API and Dummy
  - Climate zones can be attached to an optimization unit; the optimizer collects per-zone readings and exposes the thermal state to the rule engine, so policies can drive mining toward the target temperature
  - Example "Solar Surplus Room Heating" policy
  - Frontend: climate zones/monitors management and a climate dashboard

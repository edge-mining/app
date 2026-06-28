# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Global Home Assistant connection status indicator in the bottom bar, always visible: green when connected, red when disconnected or not configured. Clicking it opens a popover with the per-service status detail and a button to jump straight to the Home Assistant settings (the External Services page lands pre-filtered on the relevant adapter) (#20).

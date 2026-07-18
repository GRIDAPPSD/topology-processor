# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0a0] - 2026-07-18

Adopts Semantic Versioning. Prior releases used CalVer (2023.6.1). This is the
first semver prerelease, an alpha of 0.4.0. The CalVer releases on PyPI are
yanked so that pip no longer resolves to them; because this is a prerelease,
installers reach it with the prerelease opt-in (pip install --pre).

### Fixed
- Canonicalize mRID before the Blazegraph get_object call so topology lookups
  match stored identifiers rather than failing silently (TO-005).

### Changed
- Bound the cim-graph dependency below the untested 0.5.0 alpha train to match
  the gridappsd-python field-bus spec: pin is `>=0.4.3a6,<0.5.0` (TO-001, TO-002).

### Added
- Test coverage for mRID canonicalization and the None-versus-empty distinction.

[0.4.0a0]: https://github.com/GRIDAPPSD/topology-processor/releases/tag/v0.4.0a0

# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2026-07-18

First stable semver release. Promotes the 0.4.0 alpha line to a stable cut and
completes the move off CalVer (2023.6.1). Published to PyPI as a bare stable
version, so `pip install gridappsd-topology-processor` resolves to it without
the prerelease opt-in.

### Added
- Deliberate-dispatch stable release workflow: a `workflow_dispatch` pipeline
  that defaults to dry-run and cuts a real release only when explicitly set to
  real. pyproject.toml is the version source of truth; the workflow tags v0.4.0
  and publishes to PyPI (TO-001).
- Test coverage for mRID canonicalization and the None-versus-empty distinction.

### Changed
- Adopt Semantic Versioning in place of CalVer, with python-semantic-release
  driving the dev prerelease channel on develop (TO-001, TO-002).
- Bound the cim-graph dependency below the untested 0.5.0 alpha train to match
  the gridappsd-python field-bus spec: pin is `>=0.4.3a6,<0.5.0` (TO-001, TO-002).

### Fixed
- Canonicalize mRID before the Blazegraph get_object call so topology lookups
  match stored identifiers rather than failing silently (TO-005).

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

[0.4.0]: https://github.com/GRIDAPPSD/topology-processor/releases/tag/v0.4.0
[0.4.0a0]: https://github.com/GRIDAPPSD/topology-processor/releases/tag/v0.4.0a0

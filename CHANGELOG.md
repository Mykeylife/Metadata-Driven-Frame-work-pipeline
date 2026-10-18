# Changelog

All notable changes to the Metadata-Driven Pipeline Framework will be documented in this file.

## [Unreleased] - 2026-10-18
### Added
- Implemented `get_active_steps()` and `get_ordered_execution_steps()` methods inside `TaskCapacityManager` to fully fulfill the unit test interface contract.
- Added comprehensive data factor governance tracking columns (`data_lineage_hash`, `quality_score`, `licensing_governance`) into the core SQL metadata DDL schemas.
- Integrated automated SHA-256 cryptographic lineage hash generation and runtime validation quality score tracking metrics into the primary execution loop.

### Fixed
- Resolved the critical `Task Capacity` mismatch failure by updating `task_manager.py` to support connection-injected database orchestration.
- Fixed unit test database fixture constraints to gracefully accommodate intentional corrupted string edge cases without hitting SQL schema integrity aborts.
- Repaired `pyproject.toml` package orchestration configs and folder-level discovery paths to resolve runner test collection failures.

## - 2026-09-22
### Added
- Implemented self-contained offline SQLite database simulation architecture (`init_simulation_db.py`).
- Integrated centralized environment parameter control mapping within `pyproject.toml`.
- Added automated `docker-compose.yml` for unified single-command system orchestrations.

### Fixed
- Overhauled `.github/workflows/` parameters to resolve path resolution discrepancies.
- Eradicated critical database runtime schema parameter mismatches on core query logic.
- Purged orphaned JavaScript configuration blueprints to eliminate dependency confusion flags.

## - 2026-09-18
### Changed
- Expanded local code testing coverage matrix requirements up toward target thresholds.
- Standardized code syntax constraints formatting across core orchestration modules.

## - 2026-09-10
### Added
- Initial architectural release of the Python-based metadata-driven pipeline framework.
- Built localized in-memory transactional monitoring tables.

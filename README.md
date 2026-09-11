# Metadata-Driven-Frame-work-pipeline
Repository to hold scaffolding for a metadata-driven ADF pipeline framework, secure-by-design templates, CI and DDL.
# CI README

This repository includes a self-contained CI job that validates the scaffold at HEAD by spinning up a local SQL Server container, applying migrations, and running integration tests.

Workflows

- .github/workflows/build-and-test.yml
  - Runs on push to main and pull requests
  - Steps:
    - Lint pipeline JSON files
    - Start a dockerized SQL Server
    - Run SQL migration scripts in sql/ddl/
    - Run pytest integration tests in tests/
    - Tear down the container

Local testing

- You can run the local tests via the provided script:
  - scripts/test/run-local-tests.sh
  - Requirements: docker, docker-compose, sqlcmd/mssql-tools installed

Task capacity (parallelism)

- A validator enforces a MAX_PARALLELISM (default 8) for metadata. See tools/validate_metadata.py. CI runs similar checks.


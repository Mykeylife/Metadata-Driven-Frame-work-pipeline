# Metadata-Driven ADF Framework

This repository contains a secure-by-design scaffold for building metadata-driven Azure Data Factory (ADF) pipelines. Key goals:

- Metadata only contains safe identifiers and parameters (no free-text SQL)
- Allowlist (TransformDefinitions) controls what transforms can run
- Child pipeline uses a Switch to map TransformId → vetted stored procedures or DataFlows
- Preflight validation pipeline checks metadata rows before execution
- CI workflow to deploy pipeline JSON via ARM and az CLI

What I changed in this commit:
- Added FK creation statement to sql/ddl/00-create-metadata-table.sql (run after TransformDefinitions exists)
- Added sample TransformDefinitions INSERTs to sql/ddl/01-create-transformdefinitions.sql
- Added sample stored procedure template and audit table in sql/ddl/03-create-sample-stored-procs.sql
- Tightened grants in sql/ddl/02-grant-exec-to-adf-mi.sql to grant EXECUTE only on specific procs

Deployment order (recommended):
1) Run sql/ddl/01-create-transformdefinitions.sql to create TransformDefinitions and sample rows
2) Run sql/ddl/00-create-metadata-table.sql to create Metadata and add the FK
3) Run sql/ddl/03-create-sample-stored-procs.sql to create sample stored procedures and TransformAudit
4) Run sql/ddl/02-grant-exec-to-adf-mi.sql after creating the ADF-managed-identity DB user

Security notes:
- Only grant ADF MI the absolute minimum permissions it needs (SELECT on metadata, EXECUTE on approved procs)
- Manage TransformDefinitions via CI/PR and DB migrations to ensure vetting
- Do not run ad-hoc SQL pulled from metadata; use stored procedures and parameterized queries

See docs/README-adf-metadata.md for next steps and CI wiring.

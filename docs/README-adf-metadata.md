# Metadata-Driven ADF Framework

This repository contains a secure-by-design scaffold for building metadata-driven Azure Data Factory (ADF) pipelines. Key goals:

- Metadata only contains safe identifiers and parameters (no free-text SQL)
- Allowlist (TransformDefinitions) controls what transforms can run
- Child pipeline uses a Switch to map TransformId → vetted stored procedures or DataFlows
- Preflight validation pipeline checks metadata rows before execution
- CI workflow to deploy pipeline JSON via ARM and az CLI

See docs/README-adf-metadata.md for detailed instructions and the security checklist.

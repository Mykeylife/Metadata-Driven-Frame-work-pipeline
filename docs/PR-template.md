# PR template for TransformDefinitions changes

When proposing changes to TransformDefinitions (adding or modifying TransformIds), please include:

- Description of the transform and expected behavior
- ExecutionType (StoredProc | DataFlow | Copy) and ExecutionTarget (stored proc name or dataflow name)
- Parameter contract (names, types, constraints)
- Security review confirmation (SQL reviewed for parameterization, no string concatenation)
- Tests (unit/integration) or test plan for validation

Changes to TransformDefinitions must be merged via PR with at least one approver and pass CI validation.

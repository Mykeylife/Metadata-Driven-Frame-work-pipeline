# Branch Protection Rules

This document outlines the recommended branch protection rules for safe deployments.

## Configuration Steps

### 1. Enable Branch Protection on `main`

**Settings → Branches → Add rule**

Configure the following:

#### ✓ Require a pull request before merging
- Require approvals: **1**
- Require review from code owners (if CODEOWNERS exists)
- Require status checks to pass before merging:
  - `build-and-test` (required)
  - `deploy` (required)

#### ✓ Require status checks to pass before merging
- **Build and Test** - All tests and linting must pass
- **Code Quality** - (Optional) CodeQL, SAST checks

#### ✓ Additional protections
- Require branches to be up to date before merging: **Enabled**
- Dismiss stale pull request approvals when new commits are pushed: **Enabled**
- Allow force pushes: **Disabled**
- Allow deletions: **Disabled**

## Status Checks Required for Merge

The following GitHub Actions checks must pass:

1. **build-and-test**
   - Python dependencies installation
   - SQL migration scripts
   - Pytest tests
   - Duration: ~5-10 minutes

2. **deploy**
   - Artifact upload
   - Deployment validation
   - Duration: ~2-5 minutes

## Enforcement Policy

### Who can bypass these rules?
- Repository administrators
- (Optional) Team leads with approval authority

### When to require bypasses?
- Hotfixes for production issues
- Security patches
- Emergency deployments (rare)

## Pre-Merge Checklist

Before approving a PR, ensure:

- [ ] All checks pass (green checkmarks)
- [ ] Code review completed
- [ ] Changes align with framework design
- [ ] SQL migrations tested locally (if applicable)
- [ ] Documentation updated
- [ ] No breaking changes without discussion

## Rollback Procedures

If deployment causes issues:

1. **Identify the problem** → Check GitHub Actions logs
2. **Revert** → Create new PR reverting the changes
3. **Hotfix** → Fix the issue in a new branch
4. **Re-deploy** → Merge after fixing

## Security Considerations

- **CODEOWNERS**: Create `.github/CODEOWNERS` to require specific reviewers
- **Require status checks**: Prevents accidental deployments
- **No force pushes**: Maintains commit history integrity
- **Audit trail**: All merges are trackable and reversible

## Example CODEOWNERS

```
# Repository-level owners
* @Mykeylife

# Framework scaffolding
/pipelines/ @Mykeylife
/sql/ @Mykeylife
/tools/ @Mykeylife

# CI/CD
/.github/workflows/ @Mykeylife
```

## Testing Branch Protection Rules

After enabling, test with a sample PR:

1. Create a test branch
2. Make minor change (e.g., update README)
3. Create PR and verify:
   - Status checks are required
   - Merging is blocked until checks pass
   - Approvals are required
4. Merge only after all conditions met

## Disable/Modify Rules

If you need to modify protection rules:

1. Go to **Settings → Branches → Branch protection rules**
2. Click the rule to edit
3. Update settings
4. Save changes (applies immediately to new PRs)

---

**Note**: These settings ensure reliable, traceable deployments. They're especially important for production branches.

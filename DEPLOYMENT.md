# Deployment Guide

This guide explains how to deploy the Metadata-Driven Framework Pipeline to Azure.

## Prerequisites

- Azure subscription
- GitHub repository access (admin rights)
- Azure CLI or Azure Portal access
- GitHub Secrets configured

## Step 1: Configure GitHub Secrets

You need to configure the following secrets in your GitHub repository:

**Settings → Secrets and variables → Actions → New repository secret**

### Required Secrets

1. **AZURE_SUBSCRIPTION_ID**
   - Found in Azure Portal → Home → Subscriptions
   - Format: UUID (e.g., `12345678-1234-1234-1234-123456789012`)

2. **AZURE_RESOURCE_GROUP**
   - The name of your Azure resource group
   - Example: `metadata-framework-rg`

3. **AZURE_WEBAPP_NAME**
   - The name of your Azure Web App or Container Instance
   - Example: `metadata-framework-app`

4. **AZURE_CREDENTIALS** (Optional but recommended)
   - Service Principal credentials for authentication
   - Format: JSON object with `clientId`, `clientSecret`, `subscriptionId`, `tenantId`

## Step 2: Set Up Azure Resources

### Option A: Using Azure Portal

1. Create a new **Web App** or **Container Instance**
2. Note the resource name and group
3. Configure environment variables as needed

### Option B: Using Azure CLI

```bash
# Create resource group
az group create --name metadata-framework-rg --location eastus

# Create App Service Plan
az appservice plan create \
  --name metadata-framework-plan \
  --resource-group metadata-framework-rg \
  --sku B1

# Create Web App
az webapp create \
  --name metadata-framework-app \
  --resource-group metadata-framework-rg \
  --plan metadata-framework-plan \
  --runtime "PYTHON:3.11"
```

## Step 3: Configure Deployment Workflow

The CI/CD pipeline is configured in `.github/workflows/azure-webapps-node.yml`.

The workflow:
1. **Builds** - Sets up Python environment, installs dependencies
2. **Tests** - Runs SQL migrations and pytest tests
3. **Deploys** - Uploads artifacts to Azure

## Step 4: Trigger Deployment

Deployments are triggered automatically when you:
- Push to the `main` branch
- Create a pull request (CI runs, deployment skipped)
- Manually trigger via `workflow_dispatch`

## Monitoring Deployments

1. Go to your repository → **Actions** tab
2. Click on the workflow run to see detailed logs
3. Check deployment status in Azure Portal

## Troubleshooting

### CI Pipeline Fails: "Dependencies lock file not found"
- ✓ **Fixed**: `package.json` and `requirements.txt` now included

### Workflow Status: "Waiting for Azure credentials"
- Add `AZURE_CREDENTIALS` secret to GitHub
- Or configure Azure authentication method

### SQL Migration Fails
- Check `sql/ddl/` directory exists with `.sql` files
- Verify SQL Server connection string in environment
- Review SQL scripts for syntax errors

### Tests Fail
- Check `tests/` directory has valid pytest tests
- Review pytest output in GitHub Actions logs
- Ensure all dependencies are in `requirements.txt`

## Security Best Practices

1. ✓ Keep secrets secure in GitHub (never commit them)
2. ✓ Use Service Principals instead of personal credentials
3. ✓ Rotate credentials regularly
4. ✓ Review branch protection rules (see BRANCH_PROTECTION.md)
5. ✓ Enable Dependabot for dependency updates

## Next Steps

1. [ ] Configure the required GitHub secrets
2. [ ] Set up Azure resources
3. [ ] Verify workflow runs successfully
4. [ ] Monitor first deployment in Azure
5. [ ] Set up branch protection rules
6. [ ] Enable status checks before merge

## References

- [GitHub Actions for Azure](https://github.com/Azure/Actions)
- [Azure Web App Deployment](https://learn.microsoft.com/en-us/azure/app-service/deploy-github-actions)
- [Azure CLI Reference](https://learn.microsoft.com/en-us/cli/azure/reference-index)

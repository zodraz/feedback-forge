# Azure Container App Environment Variable Scripts

## Overview

These scripts help manage environment variables for Azure Container Apps, syncing them from your local `.env` file.

## Scripts

### 1. `set-container-env.sh` - Set Environment Variables

Sets all environment variables from `.env` to your Azure Container App.

**Before running:**
1. Edit the script and update these values:
   ```bash
   RESOURCE_GROUP="feedbackforge-rg"  # Your resource group name
   CONTAINER_APP_NAME="feedbackforge-backend"
   ```

2. Make sure you're logged into Azure:
   ```bash
   az login
   ```

3. Run the script:
   ```bash
   ./scripts/set-container-env.sh
   ```

The script will:
- ✓ Read all variables from `.env`
- ✓ Show you which variables will be set
- ✓ Ask for confirmation before proceeding
- ✓ Update the container app (triggers automatic restart)
- ✓ Skip empty variables automatically

### 2. `check-container-env.sh` - Check Current Variables

View currently configured environment variables in your Container App.

**Usage:**
```bash
./scripts/check-container-env.sh
```

## Finding Your Resource Group

If you don't know your resource group name:

```bash
# List all container apps
az containerapp list --output table

# Or search by name
az containerapp list --query "[?contains(name, 'feedbackforge')]" --output table
```

## Troubleshooting

### Error: "Resource group not found"
```bash
# List all resource groups
az group list --output table
```

### Error: "Container app not found"
```bash
# List container apps in a resource group
az containerapp list --resource-group YOUR_RG_NAME --output table
```

### Check if update worked
```bash
# View logs
az containerapp logs show \
  --name feedbackforge-backend \
  --resource-group YOUR_RG_NAME \
  --follow

# Check running status
az containerapp show \
  --name feedbackforge-backend \
  --resource-group YOUR_RG_NAME \
  --query properties.runningStatus
```

## Security Notes

⚠️ **Important:** These scripts read secrets from `.env` and upload them to Azure. Make sure:
- Your `.env` is in `.gitignore` (it already is)
- You have appropriate Azure RBAC permissions
- You're on a secure connection when running these scripts

## Alternative: Manual Setup via Azure Portal

If you prefer using the Azure Portal:

1. Go to Azure Portal → Container Apps
2. Select `feedbackforge-backend`
3. Go to **Settings** → **Environment variables**
4. Click **+ Add** for each variable
5. Restart the container app

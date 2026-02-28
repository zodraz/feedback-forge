# GitHub Actions - Azure Container Registry Setup

This guide explains how to configure GitHub Actions to build and push Docker images to Azure Container Registry (ACR).

## 📋 Prerequisites

- Azure account with an active subscription
- Azure Container Registry created
- Repository access to configure GitHub secrets
- Azure CLI installed (for setup)

## 🚀 Quick Setup

### Step 1: Create Azure Container Registry

```bash
# Login to Azure
az login

# Set variables
RESOURCE_GROUP="feedbackforge-rg"
ACR_NAME="feedbackforgeacr"  # Must be globally unique, lowercase, alphanumeric only
LOCATION="eastus"

# Create resource group (if not exists)
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create Azure Container Registry
az acr create \
  --resource-group $RESOURCE_GROUP \
  --name $ACR_NAME \
  --sku Basic \
  --admin-enabled true

# Get ACR login server
az acr show --name $ACR_NAME --query loginServer --output tsv
# Output: feedbackforgeacr.azurecr.io
```

### Step 2: Get ACR Credentials

```bash
# Get ACR username
az acr credential show --name $ACR_NAME --query username --output tsv

# Get ACR password
az acr credential show --name $ACR_NAME --query "passwords[0].value" --output tsv
```

**Save these values - you'll need them for GitHub secrets!**

### Step 3: Configure GitHub Secrets

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** and add the following:

| Secret Name | Value | Example |
|-------------|-------|---------|
| `ACR_REGISTRY` | ACR login server | `feedbackforgeacr.azurecr.io` |
| `ACR_USERNAME` | ACR username | `feedbackforgeacr` |
| `ACR_PASSWORD` | ACR password | `***` (from step 2) |

### Step 4: Push to Trigger Build

```bash
# Commit the workflow file
git add .github/workflows/docker-build-push.yml
git commit -m "Add GitHub Actions workflow for ACR"
git push origin main

# Or trigger manually
# Go to Actions → Build and Push Docker Images to ACR → Run workflow
```

## 🔧 Workflow Features

### Triggers

The workflow runs on:
- **Push to `main` or `develop` branches** - Builds and pushes images
- **Push tags starting with `v`** (e.g., `v1.0.0`) - Creates version tags
- **Pull requests to `main`** - Builds only (doesn't push)
- **Manual trigger** - Via GitHub Actions UI

### Image Tagging Strategy

Images are tagged with:
- `latest` - For main branch pushes
- `main`, `develop` - Branch name
- `v1.0.0`, `v1.0` - Semantic version tags
- `main-abc1234` - Branch + commit SHA
- `pr-123` - Pull request number

### Images Built

Three images are created:
1. **Backend** - `{ACR_REGISTRY}/feedbackforge-backend`
2. **Dashboard** - `{ACR_REGISTRY}/feedbackforge-dashboard`
3. **FAQs** - `{ACR_REGISTRY}/feedbackforge-faqs`

### Build Optimizations

- **Docker Buildx** - Multi-platform builds
- **Layer caching** - Speeds up subsequent builds
- **Parallel builds** - All images build concurrently
- **Build summary** - Shows all tags in GitHub Actions summary

## 📦 Using the Images

### Pull Images Locally

```bash
# Login to ACR
az acr login --name feedbackforgeacr

# Pull images
docker pull feedbackforgeacr.azurecr.io/feedbackforge-backend:latest
docker pull feedbackforgeacr.azurecr.io/feedbackforge-dashboard:latest
docker pull feedbackforgeacr.azurecr.io/feedbackforge-faqs:latest
```

### Update docker-compose.yml for ACR

```yaml
services:
  backend:
    image: feedbackforgeacr.azurecr.io/feedbackforge-backend:latest
    # Remove build section
    ports:
      - "8081:8081"
    env_file:
      - .env

  dashboard:
    image: feedbackforgeacr.azurecr.io/feedbackforge-dashboard:latest
    ports:
      - "3000:3000"

  faqs:
    image: feedbackforgeacr.azurecr.io/feedbackforge-faqs:latest
    ports:
      - "3002:3002"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

### Deploy with Docker Compose

```bash
# Login to ACR
az acr login --name feedbackforgeacr

# Pull and run
docker-compose pull
docker-compose up -d
```

## 🏷️ Version Tags

### Create a Release

```bash
# Tag a version
git tag v1.0.0
git push origin v1.0.0

# This creates images tagged:
# - feedbackforgeacr.azurecr.io/feedbackforge-backend:v1.0.0
# - feedbackforgeacr.azurecr.io/feedbackforge-backend:v1.0
# - feedbackforgeacr.azurecr.io/feedbackforge-backend:latest
```

### Use Specific Versions

```yaml
# In docker-compose.yml or deployment
services:
  backend:
    image: feedbackforgeacr.azurecr.io/feedbackforge-backend:v1.0.0
```

## 🔐 Security Best Practices

### Use Service Principal (Recommended for Production)

Instead of admin credentials, use a service principal:

```bash
# Create service principal
ACR_REGISTRY_ID=$(az acr show --name $ACR_NAME --query id --output tsv)

az ad sp create-for-rbac \
  --name "github-actions-feedbackforge" \
  --role acrpush \
  --scopes $ACR_REGISTRY_ID

# Output contains appId and password - use these for GitHub secrets
```

Update GitHub secrets:
- `ACR_USERNAME` → `appId` from output
- `ACR_PASSWORD` → `password` from output

### Enable Vulnerability Scanning

```bash
# Enable Microsoft Defender for Containers
az acr update --name $ACR_NAME --resource-group $RESOURCE_GROUP --anonymous-pull-enabled false
```

### Limit Token Scope

```bash
# Create scope map for specific repos
az acr scope-map create \
  --name feedbackforge-push \
  --registry $ACR_NAME \
  --repository feedbackforge-backend content/write \
  --repository feedbackforge-dashboard content/write \
  --repository feedbackforge-faqs content/write

# Create token
az acr token create \
  --name github-actions-token \
  --registry $ACR_NAME \
  --scope-map feedbackforge-push
```

## 🌍 Deploy to Azure Services

### Azure Container Instances

```bash
# Deploy backend
az container create \
  --resource-group $RESOURCE_GROUP \
  --name feedbackforge-backend \
  --image feedbackforgeacr.azurecr.io/feedbackforge-backend:latest \
  --registry-login-server feedbackforgeacr.azurecr.io \
  --registry-username $ACR_USERNAME \
  --registry-password $ACR_PASSWORD \
  --dns-name-label feedbackforge-backend \
  --ports 8081 \
  --environment-variables \
    COSMOS_DB_ENDPOINT=$COSMOS_DB_ENDPOINT \
    COSMOS_DB_KEY=$COSMOS_DB_KEY
```

### Azure App Service

```bash
# Create App Service plan
az appservice plan create \
  --name feedbackforge-plan \
  --resource-group $RESOURCE_GROUP \
  --is-linux \
  --sku B1

# Create web app
az webapp create \
  --resource-group $RESOURCE_GROUP \
  --plan feedbackforge-plan \
  --name feedbackforge-backend \
  --deployment-container-image-name feedbackforgeacr.azurecr.io/feedbackforge-backend:latest

# Configure ACR credentials
az webapp config container set \
  --name feedbackforge-backend \
  --resource-group $RESOURCE_GROUP \
  --docker-custom-image-name feedbackforgeacr.azurecr.io/feedbackforge-backend:latest \
  --docker-registry-server-url https://feedbackforgeacr.azurecr.io \
  --docker-registry-server-user $ACR_USERNAME \
  --docker-registry-server-password $ACR_PASSWORD
```

### Azure Kubernetes Service (AKS)

```bash
# Attach ACR to AKS
az aks update \
  --name feedbackforge-aks \
  --resource-group $RESOURCE_GROUP \
  --attach-acr $ACR_NAME

# Deploy using kubectl
kubectl create deployment feedbackforge-backend \
  --image=feedbackforgeacr.azurecr.io/feedbackforge-backend:latest
```

## 📊 Monitoring Builds

### View Workflow Runs

1. Go to your repository on GitHub
2. Click **Actions** tab
3. Select **Build and Push Docker Images to ACR**
4. View build logs and summaries

### Check ACR Repositories

```bash
# List repositories
az acr repository list --name $ACR_NAME --output table

# List tags for an image
az acr repository show-tags \
  --name $ACR_NAME \
  --repository feedbackforge-backend \
  --output table

# Get image details
az acr repository show \
  --name $ACR_NAME \
  --repository feedbackforge-backend \
  --output table
```

## 🐛 Troubleshooting

### Build Fails with Authentication Error

```bash
# Verify ACR credentials
az acr credential show --name $ACR_NAME

# Check if admin user is enabled
az acr update --name $ACR_NAME --admin-enabled true

# Regenerate password
az acr credential renew --name $ACR_NAME --password-name password
```

### Image Push Fails

```bash
# Check ACR storage
az acr check-health --name $ACR_NAME

# Verify network connectivity
az acr check-name --name $ACR_NAME

# Check quota
az acr show-usage --name $ACR_NAME --output table
```

### Docker Build Fails

```bash
# Test build locally first
docker build -t test-backend -f feedbackforge/Dockerfile .

# Check .dockerignore
cat .dockerignore

# View full build logs in GitHub Actions
```

## 💰 Cost Optimization

### Choose Right SKU

- **Basic** - $5/month - For development/testing
- **Standard** - $20/month - For production (recommended)
- **Premium** - $50/month - For geo-replication, private endpoints

### Clean Old Images

```bash
# Delete untagged manifests
az acr repository show-manifests \
  --name $ACR_NAME \
  --repository feedbackforge-backend \
  --query "[?tags[0]==null].digest" -o tsv \
  | xargs -I% az acr repository delete \
    --name $ACR_NAME \
    --image feedbackforge-backend@% \
    --yes

# Set retention policy (Premium SKU only)
az acr config retention update \
  --registry $ACR_NAME \
  --status enabled \
  --days 30 \
  --type UntaggedManifests
```

### Use Storage Lifecycle

```bash
# Enable storage auto-purge (Premium SKU)
az acr config retention update \
  --registry $ACR_NAME \
  --status enabled \
  --days 30
```

## 📚 Additional Resources

- [Azure Container Registry Documentation](https://docs.microsoft.com/azure/container-registry/)
- [GitHub Actions Docker Documentation](https://docs.github.com/en/actions/publishing-packages/publishing-docker-images)
- [Azure Container Instances](https://docs.microsoft.com/azure/container-instances/)
- [Docker Build Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)

---

**Status**: ✅ GitHub Actions ACR Integration Complete
**Created**: 2026-02-28
**Workflow File**: `.github/workflows/docker-build-push.yml`

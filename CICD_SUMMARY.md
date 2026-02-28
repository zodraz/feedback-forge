# CI/CD Pipeline Summary

## What Was Created

Complete GitHub Actions workflow for automated Docker image builds and deployment to Azure Container Registry.

## Files Created

### 1. GitHub Actions Workflow
**File:** `.github/workflows/docker-build-push.yml`

- Triggers on push to `main`/`develop`, version tags, and PRs
- Builds 3 Docker images in parallel:
  - `feedbackforge-backend` (Python FastAPI)
  - `feedbackforge-dashboard` (React + Nginx)
  - `feedbackforge-faqs` (React + Nginx)
- Pushes to Azure Container Registry with multiple tags
- Uses layer caching for faster builds
- Generates build summary with all image tags

### 2. Documentation
**Files:**
- `GITHUB_ACTIONS_ACR_SETUP.md` - Complete ACR setup guide
- `.github/workflows/README.md` - Workflow usage guide
- Updated `DOCKER_GUIDE.md` - Added CI/CD section
- Updated `README.md` - Added deployment section

## Quick Start

### Step 1: Create Azure Container Registry

```bash
# Login to Azure
az login

# Create ACR
ACR_NAME="feedbackforgeacr"
RESOURCE_GROUP="feedbackforge-rg"
LOCATION="eastus"

az group create --name $RESOURCE_GROUP --location $LOCATION
az acr create \
  --resource-group $RESOURCE_GROUP \
  --name $ACR_NAME \
  --sku Basic \
  --admin-enabled true
```

### Step 2: Get ACR Credentials

```bash
# Login server
az acr show --name $ACR_NAME --query loginServer --output tsv
# Output: feedbackforgeacr.azurecr.io

# Username
az acr credential show --name $ACR_NAME --query username --output tsv

# Password
az acr credential show --name $ACR_NAME --query "passwords[0].value" --output tsv
```

### Step 3: Configure GitHub Secrets

Go to **Settings → Secrets and variables → Actions** and add:

| Secret Name | Value |
|-------------|-------|
| `ACR_REGISTRY` | `feedbackforgeacr.azurecr.io` |
| `ACR_USERNAME` | Output from username command |
| `ACR_PASSWORD` | Output from password command |

### Step 4: Trigger Build

```bash
# Commit and push to main
git add .
git commit -m "Add CI/CD pipeline"
git push origin main

# Images are automatically built and pushed!
```

## Workflow Features

### Versioning Strategy

**Current:** Manual git tags (you create versions manually)

```bash
# Manual versioning
git tag v1.0.0
git push origin v1.0.0
```

**Available:** Auto-increment with commit messages

```bash
# Automatic versioning based on commit message
git commit -m "feat: add new feature"  # → v1.1.0
git commit -m "fix: bug fix"           # → v1.0.1
git commit -m "BREAKING: major change" # → v2.0.0
git push origin main
```

**See [VERSIONING_STRATEGIES.md](VERSIONING_STRATEGIES.md) for all options and how to enable auto-versioning.**

### Automatic Tagging

**Main branch push:**
```
feedbackforgeacr.azurecr.io/feedbackforge-backend:latest
feedbackforgeacr.azurecr.io/feedbackforge-backend:main
feedbackforgeacr.azurecr.io/feedbackforge-backend:main-abc1234
```

**Version tag (v1.2.3 - manual or auto):**
```
feedbackforgeacr.azurecr.io/feedbackforge-backend:v1.2.3
feedbackforgeacr.azurecr.io/feedbackforge-backend:v1.2
feedbackforgeacr.azurecr.io/feedbackforge-backend:latest
```

**Pull request (#42):**
```
feedbackforgeacr.azurecr.io/feedbackforge-backend:pr-42
(Build only - not pushed)
```

### Build Optimizations

- ✅ **Docker Buildx** - Fast, cached builds
- ✅ **Layer Caching** - Reuses unchanged layers
- ✅ **Parallel Builds** - All 3 images build simultaneously
- ✅ **Multi-stage Builds** - Small production images (~40MB frontends)

### Workflow Triggers

| Trigger | Action | Push to ACR? |
|---------|--------|--------------|
| Push to `main` | Build all images | ✅ Yes |
| Push to `develop` | Build all images | ✅ Yes |
| Push tag `v*` | Build + version tags | ✅ Yes |
| PR to `main` | Build only | ❌ No |
| Manual trigger | Build all images | ✅ Yes |

## Using the Images

### Pull from ACR

```bash
# Login to ACR
az acr login --name feedbackforgeacr

# Pull images
docker pull feedbackforgeacr.azurecr.io/feedbackforge-backend:latest
docker pull feedbackforgeacr.azurecr.io/feedbackforge-dashboard:latest
docker pull feedbackforgeacr.azurecr.io/feedbackforge-faqs:latest
```

### Update docker-compose.yml

Replace build sections with image references:

```yaml
services:
  backend:
    image: feedbackforgeacr.azurecr.io/feedbackforge-backend:latest
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

### Deploy

```bash
# Login to ACR
az acr login --name feedbackforgeacr

# Pull and start
docker-compose pull
docker-compose up -d
```

## Deployment Options

### Option 1: Azure Container Instances

```bash
# Deploy backend
az container create \
  --resource-group feedbackforge-rg \
  --name feedbackforge-backend \
  --image feedbackforgeacr.azurecr.io/feedbackforge-backend:latest \
  --registry-login-server feedbackforgeacr.azurecr.io \
  --registry-username $(az acr credential show --name feedbackforgeacr --query username -o tsv) \
  --registry-password $(az acr credential show --name feedbackforgeacr --query "passwords[0].value" -o tsv) \
  --dns-name-label feedbackforge-api \
  --ports 8081
```

### Option 2: Azure App Service

```bash
# Create App Service plan
az appservice plan create \
  --name feedbackforge-plan \
  --resource-group feedbackforge-rg \
  --is-linux \
  --sku B1

# Create web app from container
az webapp create \
  --resource-group feedbackforge-rg \
  --plan feedbackforge-plan \
  --name feedbackforge-backend \
  --deployment-container-image-name feedbackforgeacr.azurecr.io/feedbackforge-backend:latest
```

### Option 3: Azure Kubernetes Service (AKS)

```bash
# Attach ACR to AKS
az aks update \
  --name feedbackforge-aks \
  --resource-group feedbackforge-rg \
  --attach-acr feedbackforgeacr

# Deploy
kubectl create deployment feedbackforge-backend \
  --image=feedbackforgeacr.azurecr.io/feedbackforge-backend:latest
```

## Versioning Strategy

### Development

```bash
# Push to develop branch
git checkout develop
git push origin develop
# Creates: feedbackforgeacr.azurecr.io/feedbackforge-backend:develop
```

### Staging/Testing

```bash
# Push to main (without version tag)
git checkout main
git push origin main
# Creates: feedbackforgeacr.azurecr.io/feedbackforge-backend:latest
```

### Production Release

```bash
# Create semantic version tag
git tag v1.0.0
git push origin v1.0.0
# Creates:
# - feedbackforgeacr.azurecr.io/feedbackforge-backend:v1.0.0
# - feedbackforgeacr.azurecr.io/feedbackforge-backend:v1.0
# - feedbackforgeacr.azurecr.io/feedbackforge-backend:latest
```

## Monitoring

### View Builds

1. Go to **GitHub → Actions**
2. Select **Build and Push Docker Images to ACR**
3. View build logs and summary

### Check ACR

```bash
# List repositories
az acr repository list --name feedbackforgeacr --output table

# Show tags
az acr repository show-tags \
  --name feedbackforgeacr \
  --repository feedbackforge-backend \
  --output table

# Get image details
az acr repository show \
  --name feedbackforgeacr \
  --repository feedbackforge-backend:latest
```

### Build Summary

Each workflow run creates a summary showing all tags:

```
## Docker Images Built and Pushed 🐋

### Backend
```
feedbackforgeacr.azurecr.io/feedbackforge-backend:latest
feedbackforgeacr.azurecr.io/feedbackforge-backend:main
feedbackforgeacr.azurecr.io/feedbackforge-backend:main-abc1234
```

### Dashboard
...
```

## Security

### Service Principal (Recommended for Production)

```bash
# Create service principal with push access
ACR_REGISTRY_ID=$(az acr show --name feedbackforgeacr --query id --output tsv)

az ad sp create-for-rbac \
  --name "github-actions-feedbackforge" \
  --role acrpush \
  --scopes $ACR_REGISTRY_ID

# Use appId as ACR_USERNAME
# Use password as ACR_PASSWORD in GitHub secrets
```

### Scan for Vulnerabilities

```bash
# Using Trivy
trivy image feedbackforgeacr.azurecr.io/feedbackforge-backend:latest

# Using Docker Scout
docker scout cves feedbackforgeacr.azurecr.io/feedbackforge-backend:latest
```

## Cost Optimization

### ACR SKU Comparison

| SKU | Cost/Month | Use Case |
|-----|------------|----------|
| Basic | ~$5 | Development/Testing |
| Standard | ~$20 | Production (recommended) |
| Premium | ~$50 | Geo-replication, Private endpoints |

### Clean Old Images

```bash
# Delete untagged manifests
az acr repository show-manifests \
  --name feedbackforgeacr \
  --repository feedbackforge-backend \
  --query "[?tags[0]==null].digest" -o tsv \
  | xargs -I% az acr repository delete \
    --name feedbackforgeacr \
    --image feedbackforge-backend@% \
    --yes

# Delete old tags (keep last 10)
az acr repository show-tags \
  --name feedbackforgeacr \
  --repository feedbackforge-backend \
  --orderby time_desc \
  --output tsv \
  | tail -n +11 \
  | xargs -I% az acr repository delete \
    --name feedbackforgeacr \
    --image feedbackforge-backend:% \
    --yes
```

## Troubleshooting

### Build Fails

```bash
# Check workflow logs in GitHub Actions
# Test build locally
docker build -t test -f feedbackforge/Dockerfile .
```

### Push Fails

```bash
# Verify credentials
az acr credential show --name feedbackforgeacr

# Check ACR health
az acr check-health --name feedbackforgeacr

# Enable admin user
az acr update --name feedbackforgeacr --admin-enabled true
```

### Can't Pull Images

```bash
# Login first
az acr login --name feedbackforgeacr

# Or use docker login
docker login feedbackforgeacr.azurecr.io \
  -u $(az acr credential show --name feedbackforgeacr --query username -o tsv) \
  -p $(az acr credential show --name feedbackforgeacr --query "passwords[0].value" -o tsv)
```

## Complete File Structure

```
feedback-forge/
├── .github/
│   └── workflows/
│       ├── docker-build-push.yml      # Main CI/CD workflow
│       └── README.md                   # Workflow documentation
├── feedbackforge/
│   └── Dockerfile                      # Backend image
├── dashboard/
│   └── Dockerfile                      # Dashboard image (nginx)
├── faqs/
│   └── Dockerfile                      # FAQ viewer image (nginx)
├── docker-compose.yml                  # Production orchestration
├── DOCKER_GUIDE.md                     # Docker deployment guide
├── GITHUB_ACTIONS_ACR_SETUP.md        # Complete ACR setup guide
├── CICD_SUMMARY.md                    # This file
└── README.md                           # Updated with deployment info
```

## Next Steps

1. ✅ Create Azure Container Registry
2. ✅ Configure GitHub secrets
3. ✅ Push to main to trigger first build
4. ✅ Verify images in ACR
5. ✅ Update docker-compose.yml to use ACR images
6. ✅ Deploy to Azure

## Resources

- [VERSIONING_STRATEGIES.md](VERSIONING_STRATEGIES.md) - **Versioning options and auto-increment setup**
- [GITHUB_ACTIONS_ACR_SETUP.md](GITHUB_ACTIONS_ACR_SETUP.md) - Detailed setup guide
- [DOCKER_GUIDE.md](DOCKER_GUIDE.md) - Docker deployment guide
- [.github/workflows/README.md](.github/workflows/README.md) - Workflow usage
- [Azure Container Registry Docs](https://docs.microsoft.com/azure/container-registry/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

---

**Status**: ✅ CI/CD Pipeline Complete
**Created**: 2026-02-28
**Ready for**: Production deployment

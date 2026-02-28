# GitHub Actions Workflows

## Available Workflows

### 1. Build and Push Docker Images to ACR ✅ ACTIVE

**File:** `docker-build-push.yml`

**Purpose:** Automatically builds and pushes Docker images to Azure Container Registry.

**Triggers:**
- Push to `main` or `develop` branches
- Version tags (e.g., `v1.0.0`)
- Pull requests to `main` (build only, no push)
- Manual trigger via GitHub UI

**Images Built:**
- `feedbackforge-backend` - Python FastAPI backend
- `feedbackforge-dashboard` - React dashboard (nginx)
- `feedbackforge-faqs` - FAQ viewer (nginx)

**Features:**
- ✅ Multi-stage builds for optimized images
- ✅ Layer caching for faster builds
- ✅ Automatic semantic versioning
- ✅ Build summaries with all tags
- ✅ Parallel image builds

### 2. Auto Version Bump (Optional)

**File:** `auto-version.yml`

**Purpose:** Automatically creates version tags based on commit messages.

**Status:** ⚪ Created but inactive (enable by committing the file)

**How it works:**
```bash
git commit -m "fix: bug fix"           # → v1.0.1
git commit -m "feat: new feature"      # → v1.1.0
git commit -m "BREAKING: major change" # → v2.0.0
git push origin main
# Automatically creates git tag and triggers Docker build
```

**To enable:**
```bash
git add .github/workflows/auto-version.yml
git commit -m "feat: enable auto-versioning"
git push origin main
```

**See:** [VERSIONING_STRATEGIES.md](../../VERSIONING_STRATEGIES.md) for details.

### 3. Semantic Release (Alternative)

**File:** `semantic-release.yml.example`

**Purpose:** Advanced versioning with conventional commits and CHANGELOG generation.

**Status:** ⚪ Example only (rename to .yml to activate)

Industry-standard approach using [Conventional Commits](https://www.conventionalcommits.org/).

**See:** [VERSIONING_STRATEGIES.md](../../VERSIONING_STRATEGIES.md) for comparison.

## Setup Required

### GitHub Secrets

Add these secrets in **Settings → Secrets and variables → Actions**:

| Secret | Description | Example |
|--------|-------------|---------|
| `ACR_REGISTRY` | ACR login server | `feedbackforgeacr.azurecr.io` |
| `ACR_USERNAME` | ACR username | `feedbackforgeacr` |
| `ACR_PASSWORD` | ACR password/token | `***` |

### Get ACR Credentials

```bash
# Login to Azure
az login

# Get login server
az acr show --name feedbackforgeacr --query loginServer --output tsv

# Get username
az acr credential show --name feedbackforgeacr --query username --output tsv

# Get password
az acr credential show --name feedbackforgeacr --query "passwords[0].value" --output tsv
```

## Usage

### Automatic Builds

```bash
# Push to main - builds and pushes with 'latest' tag
git push origin main

# Create version tag - builds and pushes with version tags
git tag v1.0.0
git push origin v1.0.0
```

### Manual Trigger

1. Go to **Actions** tab
2. Select **Build and Push Docker Images to ACR**
3. Click **Run workflow**
4. Select branch and click **Run**

### Pull Request Builds

Pull requests to `main` trigger builds but don't push to registry:
```bash
git checkout -b feature/new-feature
git push origin feature/new-feature
# Open PR to main - workflow runs build only
```

## Image Tags Generated

### Main Branch Push

```
feedbackforgeacr.azurecr.io/feedbackforge-backend:latest
feedbackforgeacr.azurecr.io/feedbackforge-backend:main
feedbackforgeacr.azurecr.io/feedbackforge-backend:main-abc1234
```

### Version Tag (v1.2.3)

```
feedbackforgeacr.azurecr.io/feedbackforge-backend:v1.2.3
feedbackforgeacr.azurecr.io/feedbackforge-backend:v1.2
feedbackforgeacr.azurecr.io/feedbackforge-backend:latest
```

### Pull Request (#42)

```
feedbackforgeacr.azurecr.io/feedbackforge-backend:pr-42
(Build only - not pushed to registry)
```

## Viewing Build Results

### GitHub Actions UI

1. Go to **Actions** tab
2. Click on workflow run
3. View build logs and summary
4. Check "Docker Images Built and Pushed" section for all tags

### Check ACR

```bash
# List all repositories
az acr repository list --name feedbackforgeacr --output table

# Show tags for backend image
az acr repository show-tags \
  --name feedbackforgeacr \
  --repository feedbackforge-backend \
  --output table

# Get manifest details
az acr repository show \
  --name feedbackforgeacr \
  --repository feedbackforge-backend:latest
```

## Using Images

### Pull from ACR

```bash
# Login to ACR
az acr login --name feedbackforgeacr

# Pull specific image
docker pull feedbackforgeacr.azurecr.io/feedbackforge-backend:latest
docker pull feedbackforgeacr.azurecr.io/feedbackforge-dashboard:v1.0.0
docker pull feedbackforgeacr.azurecr.io/feedbackforge-faqs:main
```

### Update docker-compose.yml

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
```

### Deploy

```bash
# Login to ACR
az acr login --name feedbackforgeacr

# Pull latest images
docker-compose pull

# Start services
docker-compose up -d
```

## Troubleshooting

### Build Fails

```bash
# Check workflow logs in GitHub Actions
# Common issues:
# - ACR credentials expired/incorrect
# - Network timeout
# - Build errors in Dockerfile

# Test build locally
docker build -t test-backend -f feedbackforge/Dockerfile .
```

### Push Fails

```bash
# Verify ACR credentials
az acr credential show --name feedbackforgeacr

# Check ACR health
az acr check-health --name feedbackforgeacr

# Ensure admin user is enabled
az acr update --name feedbackforgeacr --admin-enabled true
```

### Can't Pull Images

```bash
# Login to ACR first
az acr login --name feedbackforgeacr

# Or use docker login
docker login feedbackforgeacr.azurecr.io \
  --username $(az acr credential show --name feedbackforgeacr --query username -o tsv) \
  --password $(az acr credential show --name feedbackforgeacr --query "passwords[0].value" -o tsv)
```

## Cache Management

Workflow uses Docker layer caching to speed up builds:
- Cache stored in ACR as `{image-name}:buildcache`
- Automatically reused on subsequent builds
- Reduces build time by ~50-70%

### Clear Build Cache

```bash
# Delete cache tag
az acr repository delete \
  --name feedbackforgeacr \
  --image feedbackforge-backend:buildcache \
  --yes
```

## Best Practices

1. **Use version tags for production:**
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

2. **Test in PR before merging:**
   - PR builds verify Dockerfile changes
   - Merge only after successful build

3. **Monitor build times:**
   - Check GitHub Actions for build duration
   - Optimize Dockerfiles if builds are slow

4. **Clean old images:**
   ```bash
   # Delete old tags
   az acr repository delete \
     --name feedbackforgeacr \
     --image feedbackforge-backend:old-tag \
     --yes
   ```

5. **Use semantic versioning:**
   - Major.Minor.Patch (e.g., `v1.2.3`)
   - Enables automatic tag generation

## Resources

- [Complete ACR Setup Guide](../../GITHUB_ACTIONS_ACR_SETUP.md)
- [Docker Deployment Guide](../../DOCKER_GUIDE.md)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Azure Container Registry Docs](https://docs.microsoft.com/azure/container-registry/)

---

**Need Help?**
See [GITHUB_ACTIONS_ACR_SETUP.md](../../GITHUB_ACTIONS_ACR_SETUP.md) for detailed setup instructions.

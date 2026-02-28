# Versioning Strategies for Docker Images

## Current Setup: Manual Versioning

The default workflow uses **manual git tags** for versioning.

### How It Works

```bash
# Push to main - NO version tag
git push origin main
# Creates tags: latest, main, main-abc1234

# Manually create version tag
git tag v1.0.0
git push origin v1.0.0
# Creates tags: v1.0.0, v1.0, latest
```

**Image tags created:**
```
feedbackforgeacr.azurecr.io/feedbackforge-backend:latest
feedbackforgeacr.azurecr.io/feedbackforge-backend:main
feedbackforgeacr.azurecr.io/feedbackforge-backend:main-abc1234
feedbackforgeacr.azurecr.io/feedbackforge-backend:v1.0.0
feedbackforgeacr.azurecr.io/feedbackforge-backend:v1.0
```

**Pros:**
- ✅ Full control over versions
- ✅ Simple and predictable
- ✅ No extra configuration needed

**Cons:**
- ❌ Must remember to tag manually
- ❌ Can forget to bump version
- ❌ No enforcement of semantic versioning

---

## Option 1: Auto-Increment with Commit Messages

**File:** `.github/workflows/auto-version.yml` (already created)

### How It Works

Automatically creates version tags based on commit messages:

```bash
# Patch version bump (1.0.0 → 1.0.1)
git commit -m "fix: Resolved bug in API"
git push origin main
# Auto-creates: v1.0.1

# Minor version bump (1.0.1 → 1.1.0)
git commit -m "feat: Add new dashboard widget"
git push origin main
# Auto-creates: v1.1.0

# Major version bump (1.1.0 → 2.0.0)
git commit -m "BREAKING: Redesign API endpoints"
git push origin main
# Auto-creates: v2.0.0
```

### Commit Message Keywords

| Prefix | Bump Type | Example |
|--------|-----------|---------|
| `fix:`, `patch:` | Patch | `fix: Button alignment` |
| `feat:`, `feature:`, `minor:` | Minor | `feat: Add export button` |
| `BREAKING:`, `major:`, `breaking:` | Major | `BREAKING: Remove old API` |

### Enable Auto-Versioning

The workflow is already created at `.github/workflows/auto-version.yml`.

**To activate:**
1. Commit and push it:
   ```bash
   git add .github/workflows/auto-version.yml
   git commit -m "feat: Add auto-versioning workflow"
   git push origin main
   ```

2. Use proper commit message format:
   ```bash
   git commit -m "feat: Add new feature"
   git push origin main
   # Automatically creates version tag and triggers Docker build
   ```

**Pros:**
- ✅ Automatic version bumping
- ✅ Enforces semantic versioning
- ✅ Creates GitHub releases automatically
- ✅ Works with existing Docker workflow

**Cons:**
- ❌ Requires specific commit message format
- ❌ Team needs to learn commit conventions

---

## Option 2: Semantic Release (Advanced)

**File:** `.github/workflows/semantic-release.yml.example`

### How It Works

Uses [Conventional Commits](https://www.conventionalcommits.org/) standard:

```bash
# Commit with conventional format
git commit -m "feat(dashboard): add dark mode toggle"
git push origin main

# Semantic Release automatically:
# 1. Analyzes commits since last release
# 2. Determines version bump (major/minor/patch)
# 3. Generates CHANGELOG.md
# 4. Creates git tag
# 5. Creates GitHub release
# 6. Triggers Docker build
```

### Conventional Commit Format

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat:` - New feature → Minor bump
- `fix:` - Bug fix → Patch bump
- `docs:` - Documentation → No bump
- `style:` - Formatting → No bump
- `refactor:` - Code refactor → No bump
- `test:` - Tests → No bump
- `chore:` - Maintenance → No bump

**Breaking Changes:**
```
feat(api): redesign endpoints

BREAKING CHANGE: All endpoints now use /api/v2 prefix
```
→ Major version bump

### Enable Semantic Release

```bash
# 1. Rename example file
mv .github/workflows/semantic-release.yml.example \
   .github/workflows/semantic-release.yml

# 2. Remove or disable auto-version.yml (choose one versioning strategy)
git rm .github/workflows/auto-version.yml

# 3. Commit with conventional format
git commit -m "feat: enable semantic release"
git push origin main
```

**Pros:**
- ✅ Industry-standard commit format
- ✅ Automatic CHANGELOG generation
- ✅ Rich release notes
- ✅ Multiple plugins available
- ✅ Widely used in open source

**Cons:**
- ❌ More complex setup
- ❌ Requires Node.js in CI
- ❌ Steeper learning curve

---

## Option 3: CalVer (Calendar Versioning)

**Format:** `YYYY.MM.DD[.MICRO]`

Create a custom workflow for date-based versions:

```yaml
- name: Generate CalVer tag
  id: calver
  run: |
    DATE=$(date +%Y.%m.%d)

    # Check if tag exists, add micro version if needed
    if git rev-parse "v$DATE" >/dev/null 2>&1; then
      MICRO=$(git tag -l "v$DATE.*" | wc -l)
      TAG="v$DATE.$MICRO"
    else
      TAG="v$DATE"
    fi

    echo "tag=$TAG" >> $GITHUB_OUTPUT

- name: Create tag
  run: |
    git tag ${{ steps.calver.outputs.tag }}
    git push origin ${{ steps.calver.outputs.tag }}
```

**Example tags:**
```
v2026.02.28       # First release today
v2026.02.28.1     # Second release today
v2026.02.28.2     # Third release today
```

**Pros:**
- ✅ Easy to see when version was released
- ✅ No need to decide bump type
- ✅ Good for continuous delivery

**Cons:**
- ❌ Doesn't indicate breaking changes
- ❌ Less common than SemVer

---

## Option 4: Build Number Versioning

**Format:** `1.0.BUILD_NUMBER`

Use GitHub Actions run number:

```yaml
- name: Generate version
  id: version
  run: |
    MAJOR=1
    MINOR=0
    BUILD=${{ github.run_number }}
    echo "tag=v$MAJOR.$MINOR.$BUILD" >> $GITHUB_OUTPUT

- name: Create tag
  run: |
    git tag ${{ steps.version.outputs.tag }}
    git push origin ${{ steps.version.outputs.tag }}
```

**Example tags:**
```
v1.0.1
v1.0.2
v1.0.3
```

**Pros:**
- ✅ Truly automatic, no input needed
- ✅ Monotonically increasing
- ✅ Simple to implement

**Cons:**
- ❌ Build number doesn't reflect significance
- ❌ Loses meaning when changing CI systems
- ❌ Not semantic

---

## Comparison Table

| Strategy | Automation | Semantic | Complexity | Best For |
|----------|------------|----------|------------|----------|
| **Manual Tags** | ❌ Manual | ✅ Yes | ⭐ Low | Small teams, full control |
| **Auto-Increment** | ✅ Auto | ✅ Yes | ⭐⭐ Medium | Teams wanting automation + semver |
| **Semantic Release** | ✅ Auto | ✅ Yes | ⭐⭐⭐ High | Open source, conventional commits |
| **CalVer** | ✅ Auto | ❌ No | ⭐⭐ Medium | Continuous delivery, SaaS |
| **Build Number** | ✅ Auto | ❌ No | ⭐ Low | Quick iteration, internal tools |

---

## Recommendations

### For This Project: Auto-Increment (Option 1) ✅

**Recommended because:**
- Already created and ready to use
- Simple commit message format
- Automatic versioning without complexity
- Creates GitHub releases
- Works seamlessly with Docker workflow

**To activate:**
```bash
git add .github/workflows/auto-version.yml
git commit -m "feat: add auto-versioning"
git push origin main
```

**Then use:**
```bash
# Bug fix
git commit -m "fix: Correct dashboard alignment"
git push origin main
# → Auto-creates v1.0.1

# New feature
git commit -m "feat: Add export to Excel"
git push origin main
# → Auto-creates v1.1.0

# Breaking change
git commit -m "BREAKING: Redesign API"
git push origin main
# → Auto-creates v2.0.0
```

### Alternative: Keep Manual (Current)

If you prefer full control, keep the current setup:

```bash
# When ready to release
git tag v1.0.0
git push origin v1.0.0
# Builds and pushes Docker images with v1.0.0 tag
```

---

## Docker Image Tag Strategy

Regardless of versioning approach, Docker images get multiple tags:

### Every Build
```
{ACR_REGISTRY}/feedbackforge-backend:main           # Branch name
{ACR_REGISTRY}/feedbackforge-backend:main-abc1234   # SHA
```

### Version Releases
```
{ACR_REGISTRY}/feedbackforge-backend:v1.2.3         # Full version
{ACR_REGISTRY}/feedbackforge-backend:v1.2           # Minor version
{ACR_REGISTRY}/feedbackforge-backend:v1             # Major version
{ACR_REGISTRY}/feedbackforge-backend:latest         # Latest release
```

### Usage in Production

**Pin to exact version (recommended):**
```yaml
services:
  backend:
    image: feedbackforgeacr.azurecr.io/feedbackforge-backend:v1.2.3
```

**Use minor version (auto-updates patches):**
```yaml
services:
  backend:
    image: feedbackforgeacr.azurecr.io/feedbackforge-backend:v1.2
    # Gets 1.2.0, 1.2.1, 1.2.2, etc.
```

**Use latest (not recommended for production):**
```yaml
services:
  backend:
    image: feedbackforgeacr.azurecr.io/feedbackforge-backend:latest
    # Gets whatever is latest - can break unexpectedly
```

---

## Migration Guide

### From Manual to Auto-Increment

```bash
# 1. Current version (manual)
git tag v1.0.0
git push origin v1.0.0

# 2. Enable auto-versioning
git add .github/workflows/auto-version.yml
git commit -m "feat: enable auto-versioning"
git push origin main

# 3. Future commits auto-version
git commit -m "feat: add new feature"
git push origin main
# Automatically becomes v1.1.0
```

### From Auto-Increment to Semantic Release

```bash
# 1. Remove auto-version workflow
git rm .github/workflows/auto-version.yml

# 2. Enable semantic release
mv .github/workflows/semantic-release.yml.example \
   .github/workflows/semantic-release.yml

# 3. Use conventional commits
git commit -m "feat(api): add new endpoint"
git push origin main
```

---

## Troubleshooting

### Auto-versioning not triggering

**Check:**
1. Workflow file is committed to `.github/workflows/`
2. Commit message contains keyword: `fix:`, `feat:`, `BREAKING:`
3. Push is to `main` branch
4. GitHub Actions is enabled in repository settings

### Version tag already exists

```bash
# Delete tag locally and remotely
git tag -d v1.0.0
git push origin :refs/tags/v1.0.0

# Or force push new tag
git tag -f v1.0.0
git push origin v1.0.0 --force
```

### Wrong version bumped

Auto-version uses commit message keywords. Fix by:
```bash
# Revert the auto-created tag
git push origin :refs/tags/v1.1.0

# Create correct tag
git tag v2.0.0
git push origin v2.0.0
```

---

**Current Status**: Manual versioning (default)
**Recommended**: Auto-increment with commit messages
**Created**: 2026-02-28

# Docker Deployment Guide for FeedbackForge

Complete guide for deploying FeedbackForge using Docker and Docker Compose.

## 📦 What's Included

### Docker Files Created

```
feedback-forge/
├── docker-compose.yml           # Production orchestration
├── docker-compose.dev.yml       # Development orchestration
├── .dockerignore               # Docker build ignore rules
├── .github/
│   └── workflows/
│       └── docker-build-push.yml  # CI/CD pipeline for ACR
├── feedbackforge/
│   ├── Dockerfile              # Backend production image
│   └── .dockerignore           # Backend specific ignores
├── dashboard/
│   ├── Dockerfile              # Dashboard production image
│   ├── Dockerfile.dev          # Dashboard development image
│   └── nginx.conf              # Nginx configuration for production
└── faqs/
    ├── Dockerfile              # FAQ viewer production image
    ├── Dockerfile.dev          # FAQ viewer development image
    └── nginx.conf              # Nginx configuration for production
```

## 🚀 Quick Start

### Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- `.env` file configured (copy from `.env.example`)

### Production Deployment

```bash
# 1. Ensure .env is configured
cp .env.example .env
nano .env  # Add your Azure credentials

# 2. Build and start all services
docker-compose up -d

# 3. Check status
docker-compose ps

# 4. View logs
docker-compose logs -f
```

**Access the services:**
- Backend API: http://localhost:8081
- Dashboard: http://localhost:3000
- FAQ Viewer: http://localhost:3002

### Development Deployment (with hot reload)

```bash
# Use development compose file
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f dashboard
```

## 🏗️ Services Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Docker Network: feedbackforge                         │
│                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │ Dashboard   │  │ FAQ Viewer  │  │   Redis     │   │
│  │ (nginx)     │  │ (nginx)     │  │   :6379     │   │
│  │ :3000       │  │ :3002       │  └──────┬──────┘   │
│  └──────┬──────┘  └──────┬──────┘         │          │
│         │                 │                │          │
│         └─────────┬───────┘                │          │
│                   │                        │          │
│         ┌─────────▼─────────────┐          │          │
│         │  Backend API          │◄─────────┘          │
│         │  (Python/FastAPI)     │                     │
│         │  :8081                │                     │
│         └───────────────────────┘                     │
│                   │                                    │
│                   ▼                                    │
│         Azure Services (External)                     │
│         • Cosmos DB                                   │
│         • OpenAI                                      │
│         • AI Search                                   │
└─────────────────────────────────────────────────────────┘
```

## 📝 Individual Service Commands

### Backend

```bash
# Build backend only
docker-compose build backend

# Start backend only
docker-compose up -d backend

# View backend logs
docker-compose logs -f backend

# Execute commands in backend
docker-compose exec backend python -m feedbackforge faq
docker-compose exec backend python -m feedbackforge workflow
```

### Dashboard

```bash
# Build dashboard
docker-compose build dashboard

# Start dashboard
docker-compose up -d dashboard

# Rebuild after code changes (production)
docker-compose build --no-cache dashboard
docker-compose up -d dashboard
```

### FAQ Viewer

```bash
# Build FAQ viewer
docker-compose build faqs

# Start FAQ viewer
docker-compose up -d faqs
```

### Redis

```bash
# Access Redis CLI
docker-compose exec redis redis-cli

# Check Redis data
docker-compose exec redis redis-cli KEYS "*"
docker-compose exec redis redis-cli GET "session:thread-123"
```

## 🔧 Configuration

### Environment Variables

The services use environment variables from `.env` file:

**Backend** (loaded from `.env`):
- `COSMOS_DB_ENDPOINT`
- `COSMOS_DB_KEY`
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_KEY`
- `AZURE_SEARCH_ENDPOINT`
- `AZURE_SEARCH_API_KEY`
- `REDIS_URL` (defaults to `redis://redis:6379`)

**Frontend** (set in docker-compose.yml):
- `VITE_API_BASE_URL` - Backend API URL
- `VITE_AG_UI_URL` - AG-UI agent endpoint

### Port Mapping

Default ports (can be changed in docker-compose.yml):

```yaml
services:
  backend:
    ports:
      - "8081:8081"  # Host:Container

  dashboard:
    ports:
      - "3000:3000"

  faqs:
    ports:
      - "3002:3002"

  redis:
    ports:
      - "6379:6379"
```

To change host ports:
```yaml
# Use different host port
ports:
  - "8082:8081"  # Access backend on port 8082
```

## 🔨 Building Images

### Build All Services

```bash
docker-compose build
```

### Build Specific Service

```bash
docker-compose build backend
docker-compose build dashboard
docker-compose build faqs
```

### Build Without Cache

```bash
docker-compose build --no-cache
```

### Build with Progress

```bash
docker-compose build --progress=plain
```

## 🚢 Running Services

### Start All Services

```bash
# Detached mode (background)
docker-compose up -d

# Attached mode (see logs)
docker-compose up
```

### Start Specific Services

```bash
docker-compose up -d backend redis
docker-compose up -d dashboard
```

### Stop Services

```bash
# Stop all
docker-compose stop

# Stop specific
docker-compose stop backend

# Stop and remove containers
docker-compose down

# Stop and remove everything (including volumes)
docker-compose down -v
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart specific
docker-compose restart backend
```

## 📊 Monitoring & Logs

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f dashboard

# Last 100 lines
docker-compose logs --tail=100 backend

# Since specific time
docker-compose logs --since="2024-01-01T12:00:00"
```

### Check Status

```bash
# List containers
docker-compose ps

# Detailed info
docker-compose ps -a

# Check resource usage
docker stats
```

### Health Checks

```bash
# Check if services are healthy
docker-compose ps

# Backend health check
curl http://localhost:8081/health

# Check specific container
docker inspect --format='{{.State.Health.Status}}' feedbackforge-backend
```

## 🐛 Debugging

### Access Container Shell

```bash
# Backend (Python)
docker-compose exec backend sh

# Dashboard (during build)
docker run -it feedbackforge-dashboard sh

# Redis
docker-compose exec redis sh
```

### View Container Details

```bash
# Inspect container
docker inspect feedbackforge-backend

# View container logs
docker logs feedbackforge-backend

# View resource usage
docker stats feedbackforge-backend
```

### Debug Build Issues

```bash
# Build with verbose output
docker-compose build --progress=plain backend

# Build without cache
docker-compose build --no-cache backend

# Check Dockerfile syntax
docker build -f feedbackforge/Dockerfile .
```

## 🔄 Development Workflow

### Hot Reload Setup

Use `docker-compose.dev.yml` for development:

```bash
# Start with hot reload
docker-compose -f docker-compose.dev.yml up -d

# Code changes in ./dashboard/src/ are automatically reflected
# Code changes in ./faqs/src/ are automatically reflected
# Backend changes require restart
```

### Update Dependencies

```bash
# Frontend (dashboard/faqs)
docker-compose exec dashboard npm install <package>
docker-compose restart dashboard

# Backend
docker-compose exec backend pip install <package>
docker-compose restart backend
```

### Run Tests

```bash
# Backend tests
docker-compose exec backend pytest

# Frontend tests
docker-compose exec dashboard npm test
```

## 📦 Production Deployment

### Automated CI/CD with GitHub Actions (Recommended)

**Images are automatically built and pushed to Azure Container Registry on every push to `main` or `develop` branches.**

See [GITHUB_ACTIONS_ACR_SETUP.md](GITHUB_ACTIONS_ACR_SETUP.md) for complete setup instructions.

Quick setup:
1. Create Azure Container Registry
2. Add GitHub secrets: `ACR_REGISTRY`, `ACR_USERNAME`, `ACR_PASSWORD`
3. Push to `main` branch - images build automatically

The workflow creates images tagged with:
- `latest` (main branch)
- Branch names (`main`, `develop`)
- Git commit SHA (`main-abc1234`)
- Semantic versions (`v1.0.0`, `v1.0`)

### Manual Build and Push (Alternative)

```bash
# Build optimized production images
docker-compose build --no-cache

# Tag for registry
docker tag feedbackforge-backend myregistry.azurecr.io/feedbackforge-backend:latest
docker tag feedbackforge-dashboard myregistry.azurecr.io/feedbackforge-dashboard:latest
docker tag feedbackforge-faqs myregistry.azurecr.io/feedbackforge-faqs:latest
```

### Push to Registry

```bash
# Login to Azure Container Registry
az acr login --name myregistry

# Push images
docker push myregistry.azurecr.io/feedbackforge-backend:latest
docker push myregistry.azurecr.io/feedbackforge-dashboard:latest
docker push myregistry.azurecr.io/feedbackforge-faqs:latest
```

### Deploy to Azure Container Instances

```bash
# Deploy using docker-compose
docker context create aci myacicontext
docker context use myacicontext
docker compose up
```

## 🔐 Security Best Practices

### 1. Never Commit Secrets

```bash
# .env file should NEVER be committed
echo ".env" >> .gitignore

# Use .env.example as template
cp .env.example .env
```

### 2. Use Docker Secrets (Swarm)

```yaml
services:
  backend:
    secrets:
      - cosmos_db_key
      - openai_key

secrets:
  cosmos_db_key:
    external: true
  openai_key:
    external: true
```

### 3. Run as Non-Root User

Already configured in production Dockerfiles using nginx user.

### 4. Scan Images for Vulnerabilities

```bash
# Using Docker Scout
docker scout cves feedbackforge-backend

# Using Trivy
trivy image feedbackforge-backend
```

## 🧹 Cleanup

### Remove Containers

```bash
# Stop and remove all containers
docker-compose down

# Remove with volumes
docker-compose down -v
```

### Remove Images

```bash
# Remove specific image
docker rmi feedbackforge-backend

# Remove all project images
docker-compose down --rmi all

# Clean everything
docker system prune -a
```

### Remove Volumes

```bash
# Remove named volumes
docker volume rm feedbackforge_redis-data

# Remove all unused volumes
docker volume prune
```

## 📈 Performance Optimization

### Multi-Stage Builds

Already implemented in production Dockerfiles:
- Frontend: Build stage (Node) → Production stage (nginx)
- Smaller final images (production images are ~30MB vs ~1GB)

### Layer Caching

Order in Dockerfile optimized for caching:
1. Package files (changes rarely)
2. Install dependencies
3. Source code (changes frequently)

### Resource Limits

Add to docker-compose.yml:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
```

## 🆘 Troubleshooting

### Issue: Container won't start

```bash
# Check logs
docker-compose logs backend

# Check if port is in use
lsof -i :8081

# Check docker daemon
systemctl status docker
```

### Issue: Environment variables not loaded

```bash
# Verify .env file exists
ls -la .env

# Check if variables are set in container
docker-compose exec backend env | grep COSMOS
```

### Issue: Can't connect to services

```bash
# Check network
docker network ls
docker network inspect feedbackforge_feedbackforge

# Check container connectivity
docker-compose exec backend ping redis
docker-compose exec dashboard wget -O- http://backend:8081/health
```

### Issue: Build fails

```bash
# Check Docker version
docker --version
docker-compose --version

# Clean build
docker-compose build --no-cache

# Check disk space
df -h
```

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [Best Practices for Writing Dockerfiles](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
- [Multi-stage Builds](https://docs.docker.com/develop/develop-images/multistage-build/)

---

**Status**: ✅ Docker Configuration Complete
**Last Updated**: 2026-02-28

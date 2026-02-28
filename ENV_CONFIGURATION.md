# Environment Configuration Guide

This guide explains how to configure environment variables for FeedbackForge services.

## Overview

FeedbackForge uses environment variables to configure API endpoints and other settings. This allows you to easily switch between different environments (local, WSL2, production) without changing code.

## Quick Setup

### 1. Backend Configuration

The main `.env` file is already configured in the project root:

```bash
# Already exists: /home/abel/git/feedback-forge/.env
```

**Key backend variables:**
- `COSMOS_DB_ENDPOINT` - Azure Cosmos DB endpoint
- `COSMOS_DB_KEY` - Cosmos DB primary key
- `AZURE_OPENAI_ENDPOINT` - Azure OpenAI endpoint
- `AZURE_OPENAI_KEY` - Azure OpenAI key
- `AZURE_SEARCH_ENDPOINT` - Azure AI Search endpoint
- `AZURE_SEARCH_API_KEY` - Azure AI Search API key

### 2. Dashboard Configuration

**Location:** `dashboard/.env`

```bash
# Copy the example file
cd dashboard
cp .env.example .env

# Edit with your configuration
nano .env
```

**Dashboard variables:**
```bash
VITE_API_BASE_URL=http://172.30.75.31:8081/api
VITE_AG_UI_URL=http://172.30.75.31:8081/agent
```

### 3. FAQ Viewer Configuration

**Location:** `faqs/.env`

```bash
# Copy the example file
cd faqs
cp .env.example .env

# Edit with your configuration
nano .env
```

**FAQ Viewer variables:**
```bash
VITE_API_BASE_URL=http://172.30.75.31:8081/api
```

## Configuration Scenarios

### Scenario 1: WSL2 + Windows Browser (Current Setup)

This is for when you run services in WSL2 but access them from a Windows browser.

**Get your WSL IP:**
```bash
hostname -I | awk '{print $1}'
# Example output: 172.30.75.31
```

**Dashboard `.env`:**
```bash
VITE_API_BASE_URL=http://172.30.75.31:8081/api
VITE_AG_UI_URL=http://172.30.75.31:8081/agent
```

**FAQ Viewer `.env`:**
```bash
VITE_API_BASE_URL=http://172.30.75.31:8081/api
```

### Scenario 2: All Services in WSL2

When accessing everything from within WSL2 (e.g., using a WSL browser).

**Dashboard `.env`:**
```bash
VITE_API_BASE_URL=http://localhost:8081/api
VITE_AG_UI_URL=http://localhost:8081/agent
```

**FAQ Viewer `.env`:**
```bash
VITE_API_BASE_URL=http://localhost:8081/api
```

### Scenario 3: Production Deployment

When deploying to production with a custom domain.

**Dashboard `.env`:**
```bash
VITE_API_BASE_URL=https://api.yourdomain.com/api
VITE_AG_UI_URL=https://api.yourdomain.com/agent
```

**FAQ Viewer `.env`:**
```bash
VITE_API_BASE_URL=https://api.yourdomain.com/api
```

## Environment Variable Naming

### Vite Projects (Dashboard, FAQ Viewer)

Vite requires environment variables to be prefixed with `VITE_` to be accessible in the browser:

- ✅ `VITE_API_BASE_URL` - Accessible in code
- ❌ `API_BASE_URL` - NOT accessible in code

**Usage in code:**
```typescript
const apiUrl = import.meta.env.VITE_API_BASE_URL;
```

### Python Backend

No prefix required. Standard environment variable access:

```python
import os
cosmos_endpoint = os.environ.get("COSMOS_DB_ENDPOINT")
```

## File Structure

```
feedback-forge/
├── .env                    # Backend environment variables
├── .env.example           # Backend template (commit to git)
├── dashboard/
│   ├── .env               # Dashboard environment variables (DO NOT commit)
│   ├── .env.example       # Dashboard template (commit to git)
│   └── .gitignore         # Ignores .env files
├── faqs/
│   ├── .env               # FAQ viewer environment variables (DO NOT commit)
│   ├── .env.example       # FAQ viewer template (commit to git)
│   └── .gitignore         # Ignores .env files
└── ENV_CONFIGURATION.md   # This file
```

## Security Best Practices

### ✅ DO:
- Keep `.env` files in `.gitignore`
- Commit `.env.example` files as templates
- Use different values for dev/staging/production
- Document all required variables in `.env.example`
- Rotate secrets regularly

### ❌ DON'T:
- Commit actual `.env` files to git
- Put secrets in `.env.example` files
- Hardcode URLs or secrets in source code
- Share `.env` files via email or chat

## Updating Configuration

After changing `.env` files, you need to restart the services:

### Dashboard:
```bash
# Stop the server (Ctrl+C), then:
cd dashboard && npm run dev
```

### FAQ Viewer:
```bash
# Stop the server (Ctrl+C), then:
cd faqs && npm run dev
```

### Backend:
```bash
# Stop the server (Ctrl+C), then:
python -m feedbackforge serve --port 8081
```

## Troubleshooting

### Variables Not Loading

**Problem:** Changes to `.env` not being picked up

**Solution:**
1. Restart the development server completely (Ctrl+C and restart)
2. Clear browser cache
3. Check variable names have `VITE_` prefix (for frontend)
4. Verify `.env` file is in the correct directory

### Connection Refused Errors

**Problem:** `ERR_CONNECTION_REFUSED` in browser

**Solution:**
1. Check if WSL IP has changed: `hostname -I`
2. Update `.env` files with new IP
3. Restart all services
4. Make sure `host: '0.0.0.0'` is set in `vite.config.ts`

### CORS Errors

**Problem:** CORS policy blocking requests

**Solution:**
1. Verify backend is running: `curl http://172.30.75.31:8081/health`
2. Check backend CORS configuration in `server.py`
3. Ensure URLs in `.env` match backend URL exactly

## Quick Reference Commands

### Get WSL IP Address:
```bash
hostname -I | awk '{print $1}'
```

### Test Backend Connection:
```bash
curl http://172.30.75.31:8081/health
```

### View Current Environment Variables:
```bash
# In dashboard or faqs directory
cat .env
```

### Copy Example to Production:
```bash
cp .env.example .env
```

## Default Values

If `.env` file is missing or a variable is not set, the code falls back to these defaults:

**Dashboard:**
- `VITE_API_BASE_URL`: `http://localhost:8081/api`
- `VITE_AG_UI_URL`: `http://localhost:8081/agent`

**FAQ Viewer:**
- `VITE_API_BASE_URL`: `http://localhost:8081/api`

**Backend:**
- Server port: `8081` (via command line: `--port 8081`)
- Host: `0.0.0.0`

## Environment Variables Reference

### Backend (.env in project root)

| Variable | Description | Example |
|----------|-------------|---------|
| `COSMOS_DB_ENDPOINT` | Azure Cosmos DB endpoint | `https://xxx.documents.azure.com:443/` |
| `COSMOS_DB_KEY` | Cosmos DB primary key | `your-key-here` |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint | `https://xxx.openai.azure.com/` |
| `AZURE_OPENAI_KEY` | Azure OpenAI API key | `your-key-here` |
| `AZURE_SEARCH_ENDPOINT` | Azure AI Search endpoint | `https://xxx.search.windows.net` |
| `AZURE_SEARCH_API_KEY` | Azure AI Search API key | `your-key-here` |
| `REDIS_URL` | Optional Redis URL for sessions | `redis://localhost:6379` |

### Frontend (dashboard/.env and faqs/.env)

| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_API_BASE_URL` | Backend API base URL | `http://172.30.75.31:8081/api` |
| `VITE_AG_UI_URL` | AG-UI agent endpoint (dashboard only) | `http://172.30.75.31:8081/agent` |

---

**Last Updated:** 2026-02-28
**Status:** ✅ Configured

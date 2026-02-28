# Quick Switch: Cosmos DB Authentication Methods

## Overview

FeedbackForge now has an explicit `COSMOS_DB_AUTH_METHOD` variable to easily switch between authentication methods.

---

## 🔄 Quick Switch Guide

### Option 1: Auto Mode (Default)
**Use key if set, otherwise DefaultAzureCredential**

```bash
# .env
COSMOS_DB_ENDPOINT=https://feedbackforge-db.documents.azure.com:443/
COSMOS_DB_AUTH_METHOD=auto  # or omit this line
COSMOS_DB_KEY=your-key-here  # Optional
```

**Behavior:**
- If `COSMOS_DB_KEY` is set → Uses primary key
- If `COSMOS_DB_KEY` is not set → Uses DefaultAzureCredential

---

### Option 2: Force Primary Key
**Always use primary key authentication**

```bash
# .env
COSMOS_DB_ENDPOINT=https://feedbackforge-db.documents.azure.com:443/
COSMOS_DB_AUTH_METHOD=primary_key  # 🔑 Force primary key
COSMOS_DB_KEY=your-primary-key-here  # REQUIRED
```

**When to use:**
- ✅ Development/testing
- ✅ Quick local setup
- ✅ When Azure AD is not available

**Requirements:**
- `COSMOS_DB_KEY` must be set
- Get key from: Azure Portal → Cosmos DB → Keys → Primary Key

---

### Option 3: Force DefaultAzureCredential
**Always use Azure AD authentication (no key needed)**

```bash
# .env
COSMOS_DB_ENDPOINT=https://feedbackforge-db.documents.azure.com:443/
COSMOS_DB_AUTH_METHOD=default_credential  # 🔐 Force Azure AD
# COSMOS_DB_KEY not needed (will be ignored if set)
```

**When to use:**
- ✅ Production deployments
- ✅ CI/CD pipelines
- ✅ Azure-hosted apps
- ✅ Better security

**Requirements:**
- Run `az login` for local development
- OR use Managed Identity in Azure
- OR set service principal env vars (AZURE_CLIENT_ID, etc.)

---

## 🎯 Quick Examples

### Switch from Primary Key to DefaultAzureCredential

**Before:**
```bash
COSMOS_DB_AUTH_METHOD=primary_key
COSMOS_DB_KEY=your-key-here
```

**After:**
```bash
COSMOS_DB_AUTH_METHOD=default_credential
# Key is ignored now
```

Then restart:
```bash
python -m feedbackforge serve
```

---

### Switch from DefaultAzureCredential to Primary Key

**Before:**
```bash
COSMOS_DB_AUTH_METHOD=default_credential
```

**After:**
```bash
COSMOS_DB_AUTH_METHOD=primary_key
COSMOS_DB_KEY=your-key-here  # Add your key
```

Then restart:
```bash
python -m feedbackforge serve
```

---

## 📊 Comparison

| Method | .env Setting | Key Required? | Azure Login? | Best For |
|--------|-------------|---------------|--------------|----------|
| **Auto** | `auto` or omitted | Optional | If no key | Flexible development |
| **Primary Key** | `primary_key` | ✅ Yes | ❌ No | Quick local setup |
| **DefaultAzureCredential** | `default_credential` | ❌ No | ✅ Yes | Production |

---

## 🔍 How to Verify

Check the server logs on startup:

### Auto Mode with Key:
```
🚀 Initializing Cosmos DB feedback store...
⚙️ Auth method: Auto (will use key if set, otherwise DefaultAzureCredential)
🔑 Using primary key authentication for Cosmos DB
✅ Using Cosmos DB for feedback storage
```

### Forced Primary Key:
```
🚀 Initializing Cosmos DB feedback store...
🔑 Auth method: Primary key (forced by COSMOS_DB_AUTH_METHOD)
🔑 Using primary key authentication for Cosmos DB
✅ Using Cosmos DB for feedback storage
```

### Forced DefaultAzureCredential:
```
🚀 Initializing Cosmos DB feedback store...
🔐 Auth method: DefaultAzureCredential (forced by COSMOS_DB_AUTH_METHOD)
🔐 Using DefaultAzureCredential for Cosmos DB
✅ Using Cosmos DB for feedback storage
```

---

## ❌ Common Errors

### Error: "COSMOS_DB_KEY is not set"
```
ValueError: COSMOS_DB_AUTH_METHOD=primary_key but COSMOS_DB_KEY is not set
```

**Fix:** Add your primary key to `.env`:
```bash
COSMOS_DB_KEY=your-key-here
```

### Error: "Request blocked by Auth"
```
(Forbidden) Request blocked by Auth feedbackforge-db : Request is blocked because principal [...] does not have required RBAC permissions
```

**Fix:** Either:
1. Switch to primary key auth:
   ```bash
   COSMOS_DB_AUTH_METHOD=primary_key
   COSMOS_DB_KEY=your-key-here
   ```
2. OR grant RBAC permissions:
   ```bash
   az cosmosdb sql role assignment create \
     --account-name feedbackforge-db \
     --resource-group feedbackforge-rg \
     --role-definition-name "Cosmos DB Built-in Data Contributor" \
     --principal-id $(az ad signed-in-user show --query id -o tsv) \
     --scope "/"
   ```

---

## 🚀 Quick Start Commands

### Test with Primary Key:
```bash
# 1. Set auth method
export COSMOS_DB_AUTH_METHOD=primary_key

# 2. Start server
python -m feedbackforge serve

# Look for: 🔑 Using primary key authentication
```

### Test with DefaultAzureCredential:
```bash
# 1. Login to Azure
az login

# 2. Set auth method
export COSMOS_DB_AUTH_METHOD=default_credential

# 3. Start server
python -m feedbackforge serve

# Look for: 🔐 Using DefaultAzureCredential
```

---

## 📝 Environment Variable Reference

```bash
# Required for Cosmos DB
COSMOS_DB_ENDPOINT=https://your-account.documents.azure.com:443/

# Authentication method (optional, default: auto)
COSMOS_DB_AUTH_METHOD=auto | primary_key | default_credential

# Primary key (required if AUTH_METHOD=primary_key)
COSMOS_DB_KEY=your-key-here

# Database and container names (optional)
COSMOS_DB_DATABASE=feedbackforge
COSMOS_DB_CONTAINER=feedback
```

---

## 🎉 Summary

**The easiest way to switch:**

1. **Want to use primary key?**
   ```bash
   COSMOS_DB_AUTH_METHOD=primary_key
   COSMOS_DB_KEY=your-key
   ```

2. **Want to use Azure AD?**
   ```bash
   COSMOS_DB_AUTH_METHOD=default_credential
   # Run: az login
   ```

3. **Want automatic selection?**
   ```bash
   COSMOS_DB_AUTH_METHOD=auto  # or omit
   ```

Just change the `.env` file and restart the server!

---

**Last Updated:** 2026-02-27

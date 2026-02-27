# Cosmos DB Authentication Guide

## Overview

FeedbackForge supports **two authentication methods** for Azure Cosmos DB:

1. **Primary Key** (Recommended for development)
2. **DefaultAzureCredential** (Recommended for production)

---

## Method 1: Primary Key Authentication (Easy Setup)

### When to Use
- ✅ Development and testing
- ✅ Quick setup
- ✅ Local development
- ⚠️ **Not recommended for production** (keys can be compromised)

### Setup Steps

#### 1. Get Your Primary Key

**Option A: Azure Portal**
1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to your Cosmos DB account
3. Click **"Keys"** in the left menu
4. Copy the **"PRIMARY KEY"**

**Option B: Azure CLI**
```bash
az cosmosdb keys list \
  --name feedbackforge-db \
  --resource-group feedbackforge-rg \
  --query primaryMasterKey \
  --output tsv
```

#### 2. Add to `.env` File

```bash
# .env
COSMOS_DB_ENDPOINT=https://feedbackforge-db.documents.azure.com:443/
COSMOS_DB_KEY=YourPrimaryKeyHereVeryLongString==  # ← Your primary key
COSMOS_DB_DATABASE=feedbackforge
COSMOS_DB_CONTAINER=feedback
```

#### 3. Start the Server

```bash
python -m feedbackforge serve --port 8080

# You'll see:
# 🚀 Initializing Cosmos DB feedback store...
# 🔑 Using primary key authentication for Cosmos DB
# ✅ Database 'feedbackforge' ready
# ✅ Container 'feedback' ready
```

### ✅ Pros and Cons

**Pros:**
- ✅ Super easy setup
- ✅ No Azure login required
- ✅ Works immediately
- ✅ Perfect for local development

**Cons:**
- ❌ Key must be kept secret
- ❌ If key is leaked, your database is compromised
- ❌ Keys don't rotate automatically
- ❌ Not good for production environments

---

## Method 2: DefaultAzureCredential (Production Ready)

### When to Use
- ✅ Production deployments
- ✅ CI/CD pipelines
- ✅ Azure-hosted applications
- ✅ Team environments
- ✅ Better security posture

### Setup Steps

#### 1. Assign Permissions

**Grant your user/service access to Cosmos DB:**

```bash
# Get your user's object ID
USER_ID=$(az ad signed-in-user show --query id -o tsv)

# Assign Cosmos DB Data Contributor role
az cosmosdb sql role assignment create \
  --account-name feedbackforge-db \
  --resource-group feedbackforge-rg \
  --role-definition-name "Cosmos DB Built-in Data Contributor" \
  --principal-id $USER_ID \
  --scope "/"
```

#### 2. Configure `.env` (No Key Needed!)

```bash
# .env
COSMOS_DB_ENDPOINT=https://feedbackforge-db.documents.azure.com:443/
# COSMOS_DB_KEY is NOT needed!
COSMOS_DB_DATABASE=feedbackforge
COSMOS_DB_CONTAINER=feedback
```

#### 3. Authenticate with Azure

**Option A: Azure CLI (Local Development)**
```bash
az login
az account show  # Verify you're logged in
```

**Option B: Managed Identity (Azure Deployments)**
```bash
# Automatically works in:
# - Azure App Service
# - Azure Functions
# - Azure Container Instances
# - Azure Virtual Machines
# No additional config needed!
```

**Option C: Service Principal (CI/CD)**
```bash
# Set environment variables
export AZURE_CLIENT_ID="your-client-id"
export AZURE_TENANT_ID="your-tenant-id"
export AZURE_CLIENT_SECRET="your-client-secret"
```

#### 4. Start the Server

```bash
python -m feedbackforge serve --port 8080

# You'll see:
# 🚀 Initializing Cosmos DB feedback store...
# 🔐 Using DefaultAzureCredential for Cosmos DB
# ✅ Database 'feedbackforge' ready
# ✅ Container 'feedback' ready
```

### ✅ Pros and Cons

**Pros:**
- ✅ No secrets to manage
- ✅ Works with Azure RBAC
- ✅ Automatic credential rotation
- ✅ Better security
- ✅ Audit trail in Azure AD
- ✅ Production-ready

**Cons:**
- ❌ More complex setup
- ❌ Requires Azure permissions
- ❌ Need to configure roles

---

## Quick Comparison

| Feature | Primary Key | DefaultAzureCredential |
|---------|-------------|------------------------|
| **Ease of Setup** | ⭐⭐⭐⭐⭐ Easy | ⭐⭐⭐ Medium |
| **Security** | ⭐⭐ Low | ⭐⭐⭐⭐⭐ High |
| **Production Ready** | ❌ No | ✅ Yes |
| **Secret Management** | Manual | Automatic |
| **Audit Trail** | ❌ No | ✅ Yes |
| **Local Dev** | ✅ Perfect | ⭐⭐⭐ Good |
| **Azure Deployments** | ⚠️ Risky | ✅ Perfect |

---

## Recommended Strategy

### For Development:
```bash
# Use primary key for quick local testing
COSMOS_DB_ENDPOINT=https://feedbackforge-db.documents.azure.com:443/
COSMOS_DB_KEY=your-primary-key-here
```

### For Production:
```bash
# Use DefaultAzureCredential with managed identity
COSMOS_DB_ENDPOINT=https://feedbackforge-db.documents.azure.com:443/
# No COSMOS_DB_KEY needed!
```

---

## How It Works

### Authentication Flow

```python
# In data_store.py
def __init__(self, endpoint: str, key: Optional[str] = None):
    if key:
        # Use primary key
        self.client = CosmosClient(endpoint, credential=key)
    else:
        # Use DefaultAzureCredential
        credential = DefaultAzureCredential()
        self.client = CosmosClient(endpoint, credential=credential)
```

### Priority Order

1. **If `COSMOS_DB_KEY` is set** → Use primary key ✅
2. **If `COSMOS_DB_KEY` is NOT set** → Use DefaultAzureCredential ✅

---

## Testing Both Methods

### Test Primary Key

```bash
# Set key
export COSMOS_DB_ENDPOINT="https://feedbackforge-db.documents.azure.com:443/"
export COSMOS_DB_KEY="YourPrimaryKeyHere=="

# Start server
python -m feedbackforge serve

# Look for:
# 🔑 Using primary key authentication for Cosmos DB
```

### Test DefaultAzureCredential

```bash
# Unset key
export COSMOS_DB_ENDPOINT="https://feedbackforge-db.documents.azure.com:443/"
unset COSMOS_DB_KEY  # Remove key

# Login
az login

# Start server
python -m feedbackforge serve

# Look for:
# 🔐 Using DefaultAzureCredential for Cosmos DB
```

---

## Troubleshooting

### Issue: "Authentication failed with primary key"

**Symptoms:**
```
⚠️ Failed to initialize Cosmos DB: Unauthorized
```

**Solutions:**
1. Verify your key is correct:
   ```bash
   az cosmosdb keys list --name feedbackforge-db --resource-group feedbackforge-rg
   ```
2. Check for extra spaces in `.env` file
3. Make sure you copied the full key (it's very long!)

### Issue: "DefaultAzureCredential failed"

**Symptoms:**
```
DefaultAzureCredential failed to retrieve a token
```

**Solutions:**

1. **For local development:**
   ```bash
   az login
   az account show
   ```

2. **Check RBAC permissions:**
   ```bash
   # Verify role assignment
   az role assignment list \
     --assignee $(az ad signed-in-user show --query id -o tsv) \
     --scope /subscriptions/YOUR-SUB-ID/resourceGroups/feedbackforge-rg
   ```

3. **For service principal:**
   ```bash
   # Verify environment variables are set
   echo $AZURE_CLIENT_ID
   echo $AZURE_TENANT_ID
   echo $AZURE_CLIENT_SECRET  # Should show ***
   ```

### Issue: "Permission denied to create database/container"

**Solution:**

Ensure you have the correct role:
```bash
az cosmosdb sql role assignment create \
  --account-name feedbackforge-db \
  --resource-group feedbackforge-rg \
  --role-definition-name "Cosmos DB Built-in Data Contributor" \
  --principal-id YOUR-USER-ID \
  --scope "/"
```

---

## Security Best Practices

### ✅ DO:
- ✅ Use primary key for local development only
- ✅ Use DefaultAzureCredential for production
- ✅ Store keys in `.env` (never commit to git!)
- ✅ Rotate keys regularly if using them
- ✅ Use managed identities in Azure
- ✅ Restrict RBAC to minimum required permissions

### ❌ DON'T:
- ❌ Commit `.env` to git
- ❌ Share primary keys in Slack/email
- ❌ Use primary keys in production
- ❌ Store keys in code
- ❌ Use admin keys when read-only keys would work

---

## Example `.env` Files

### Development (Primary Key)
```bash
# .env.development
COSMOS_DB_ENDPOINT=https://feedbackforge-dev.documents.azure.com:443/
COSMOS_DB_KEY=PrimaryKeyForDevEnvironment==
COSMOS_DB_DATABASE=feedbackforge-dev
```

### Staging (DefaultAzureCredential)
```bash
# .env.staging
COSMOS_DB_ENDPOINT=https://feedbackforge-staging.documents.azure.com:443/
# No key - uses managed identity
COSMOS_DB_DATABASE=feedbackforge-staging
```

### Production (DefaultAzureCredential)
```bash
# .env.production
COSMOS_DB_ENDPOINT=https://feedbackforge-prod.documents.azure.com:443/
# No key - uses managed identity
COSMOS_DB_DATABASE=feedbackforge-prod
```

---

## Summary

### Quick Start (Primary Key)
```bash
# 1. Get key from Azure Portal
# 2. Add to .env:
COSMOS_DB_ENDPOINT=https://your-account.documents.azure.com:443/
COSMOS_DB_KEY=your-primary-key==

# 3. Start server
python -m feedbackforge serve
```

### Production Setup (DefaultAzureCredential)
```bash
# 1. Assign RBAC role
az cosmosdb sql role assignment create ...

# 2. Add to .env:
COSMOS_DB_ENDPOINT=https://your-account.documents.azure.com:443/
# No key needed!

# 3. Login
az login

# 4. Start server
python -m feedbackforge serve
```

**Both methods work seamlessly - choose based on your environment!** 🎉

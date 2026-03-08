# Azure Redis Cache Setup

## Configuration

Your Azure Redis Cache is configured at:
- **Host**: `feedbackforge-cache.swedencentral.redis.azure.net`
- **Port**: `6380` (SSL port) or `10000` (if clustered)
- **SSL Required**: Yes

**Note**: Azure Redis Cache typically uses:
- Port `6380` for SSL connections (standard)
- Port `6379` for non-SSL (if enabled)
- Port `10000` for cluster proxy (if clustering is enabled)

## Steps to Configure

### 1. Get Your Access Key

From Azure Portal:
1. Navigate to your Redis Cache: `feedbackforge-cache`
2. Go to **Settings** > **Access keys**
3. Copy the **Primary** or **Secondary** access key

### 2. Update Your `.env` File

Add or update the `REDIS_URL` in your `.env` file:

```bash
# Azure Redis Cache (SSL enabled)
REDIS_URL=rediss://:YOUR_ACCESS_KEY_HERE@feedbackforge-cache.swedencentral.redis.azure.net:10000/0
```

**Important Notes:**
- Use `rediss://` (double 's') for SSL connection
- Include the colon `:` before the access key
- The `/0` at the end specifies database 0 (default)
- Replace `YOUR_ACCESS_KEY_HERE` with your actual access key from Azure Portal

### 3. Changes Made to Docker Compose

Both `docker-compose.yml` and `docker-compose.dev.yml` have been updated:

✅ Removed dependency on local Redis container
✅ Changed `REDIS_URL` to use environment variable
✅ Commented out local Redis service (can be re-enabled if needed)

### 4. Verify Connection

After updating your `.env`, restart the services:

```bash
# Stop existing containers
docker-compose down

# Start with Azure Redis
docker-compose up -d

# Check logs
docker-compose logs -f backend
```

You should see:
```
✅ Using Redis for session management
```

If connection fails, you'll see:
```
⚠️ Redis connection failed: ... Using in-memory sessions.
```

## Troubleshooting

### "Connection closed by server" Error

This is usually an SSL/TLS or port configuration issue. Try these steps:

1. **Try the standard SSL port (6380) instead of 10000**:
   ```bash
   REDIS_URL=rediss://:YOUR_KEY@feedbackforge-cache.swedencentral.redis.azure.net:6380/0
   ```

2. **Check if non-SSL port is enabled** (Azure Portal > Settings > Advanced settings):
   - If enabled, try port 6379 without SSL:
     ```bash
     REDIS_URL=redis://:YOUR_KEY@feedbackforge-cache.swedencentral.redis.azure.net:6379/0
     ```

3. **Verify clustering is enabled/disabled**:
   - If clustering is OFF, use port 6380
   - If clustering is ON, use port 10000

4. **Check the connection string format**:
   - Ensure colon `:` before the access key
   - No spaces in the URL
   - Database number at the end (usually `/0`)

### Connection Timeout
- Ensure your network/firewall allows outbound connections
- Check Azure Redis firewall rules (Settings > Firewall)
- Add your IP or enable "Allow access from Azure services"
- Verify the host and port are correct

### Authentication Failed
- Double-check your access key (no spaces, exact copy)
- Try regenerating the access key in Azure Portal
- Ensure you're using the PRIMARY or SECONDARY key, not connection string

### SSL/TLS Certificate Errors
- The code now automatically disables certificate verification for Azure Redis
- Ensure you're using `rediss://` (double 's') not `redis://` for SSL ports
- Port 6380 requires SSL
- Port 6379 only works if non-SSL port is enabled in Azure

## Switching Back to Local Redis

If needed, you can switch back to local Redis:

1. Uncomment the Redis service in `docker-compose.yml`:
   ```yaml
   redis:
     image: redis:7-alpine
     # ... rest of config
   ```

2. Uncomment the dependency in backend service:
   ```yaml
   depends_on:
     - redis
   ```

3. Update `.env`:
   ```bash
   REDIS_URL=redis://redis:6379
   ```

## Environment Variable Format

```bash
# Azure Redis Cache (Production)
REDIS_URL=rediss://:ACCESS_KEY@HOST:PORT/DATABASE

# Local Redis (Development)
REDIS_URL=redis://localhost:6379
```

Where:
- `rediss://` = SSL enabled (required for Azure)
- `:ACCESS_KEY` = Your Redis access key (colon is required)
- `@HOST:PORT` = Redis endpoint and port
- `/DATABASE` = Database number (0-15, typically use 0)

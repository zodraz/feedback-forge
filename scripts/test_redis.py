#!/usr/bin/env python3
"""
Test Redis connection to Azure Redis Cache.

Usage:
    python scripts/test_redis.py

Or specify a custom Redis URL:
    python scripts/test_redis.py "rediss://:KEY@HOST:PORT/0"
"""

import asyncio
import os
import ssl
import sys


async def test_redis_connection(redis_url: str):
    """Test Redis connection with detailed error reporting."""
    print(f"🔍 Testing Redis connection...")
    print(f"   URL: {redis_url.split(':')[1] if ':' in redis_url else redis_url[:50]}...")

    # Parse URL to show details
    if '@' in redis_url:
        parts = redis_url.split('@')
        host_port = parts[1].split('/')[0]
        print(f"   Host: {host_port}")

    try:
        import redis.asyncio as redis

        # Configure SSL for Azure Redis Cache
        ssl_params = {}
        if redis_url.startswith("rediss://"):
            ssl_params = {
                "ssl_cert_reqs": ssl.CERT_NONE,
                "ssl_check_hostname": False,
            }
            print("   🔐 SSL enabled (certificate verification disabled)")

        print("\n📡 Creating Redis client...")
        redis_client = redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=10,
            socket_timeout=10,
            **ssl_params
        )

        print("📡 Sending PING command...")
        result = await redis_client.ping()

        if result:
            print("✅ SUCCESS! Redis connection is working!")

            # Try basic operations
            print("\n🧪 Testing basic operations...")
            await redis_client.set("test_key", "test_value", ex=60)
            print("   ✅ SET operation successful")

            value = await redis_client.get("test_key")
            print(f"   ✅ GET operation successful: {value}")

            await redis_client.delete("test_key")
            print("   ✅ DELETE operation successful")

            print("\n🎉 All tests passed! Redis is ready to use.")
            return True
        else:
            print("❌ PING failed")
            return False

    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        print(f"   Error type: {type(e).__name__}")

        # Provide specific troubleshooting based on error
        error_str = str(e).lower()

        if "connection refused" in error_str:
            print("\n💡 Troubleshooting:")
            print("   - Check if the host and port are correct")
            print("   - Verify firewall rules in Azure Portal")

        elif "connection closed" in error_str or "connection reset" in error_str:
            print("\n💡 Troubleshooting:")
            print("   - Try port 6380 (standard SSL port) instead of 10000")
            print("   - Try port 6379 (non-SSL, if enabled)")
            print("   - Check if clustering is enabled/disabled")

        elif "authentication" in error_str or "auth" in error_str:
            print("\n💡 Troubleshooting:")
            print("   - Double-check your access key")
            print("   - Ensure the format is: rediss://:KEY@host:port/0")
            print("   - Note the colon ':' before the key")

        elif "ssl" in error_str or "certificate" in error_str:
            print("\n💡 Troubleshooting:")
            print("   - Ensure you're using 'rediss://' (double s) for SSL")
            print("   - Port 6380 requires SSL, port 6379 doesn't")

        elif "timeout" in error_str:
            print("\n💡 Troubleshooting:")
            print("   - Check network/firewall settings")
            print("   - Verify Azure Redis firewall rules")
            print("   - Ensure you can reach the host from your network")

        return False
    finally:
        try:
            await redis_client.aclose()
        except:
            pass


def main():
    """Main entry point."""
    # Try to get Redis URL from command line, .env, or environment
    if len(sys.argv) > 1:
        redis_url = sys.argv[1]
    else:
        # Try to load from .env
        try:
            from dotenv import load_dotenv
            load_dotenv()
            print("📄 Loaded .env file")
        except ImportError:
            print("ℹ️  python-dotenv not available, reading from environment only")

        redis_url = os.environ.get("REDIS_URL")

        if not redis_url:
            print("❌ Error: REDIS_URL not found")
            print("\nUsage:")
            print("  1. Set REDIS_URL in .env file")
            print("  2. Set REDIS_URL environment variable")
            print("  3. Pass as argument: python scripts/test_redis.py 'rediss://:KEY@HOST:PORT/0'")
            sys.exit(1)

    # Run the test
    success = asyncio.run(test_redis_connection(redis_url))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

# Copyright (c) 2024, FalkorDB
# Copyrights licensed under the New BSD License
# See the accompanying LICENSE.txt file for terms.
"""
Async redislite client

This module provides async versions of the Redis client that work with
the embedded Redis server. It uses redis.asyncio for async operations
while managing the embedded server lifecycle.
"""
import asyncio
import logging
from typing import Optional

import redis.asyncio as aioredis

from .client import RedisMixin, Redis as SyncRedis

logger = logging.getLogger(__name__)


class AsyncRedis(RedisMixin):
    """
    Async version of the Redis client for use with redislite.
    
    This class manages the embedded Redis server but provides async
    operations for Redis commands.
    
    Example:
        >>> import asyncio
        >>> from redislite.async_client import AsyncRedis
        >>> 
        >>> async def main():
        ...     redis_conn = AsyncRedis('/tmp/redis.db')
        ...     await redis_conn.set('key', 'value')
        ...     value = await redis_conn.get('key')
        ...     print(value)
        ...     await redis_conn.close()
        >>> 
        >>> asyncio.run(main())
    """
    
    def __init__(
        self,
        dbfilename: Optional[str] = None,
        serverconfig: Optional[dict] = None,
        **kwargs
    ):
        """
        Initialize the async Redis client with embedded server.
        
        Args:
            dbfilename: Path to the Redis database file
            serverconfig: Additional Redis server configuration
            **kwargs: Additional arguments passed to the async Redis client
        """
        # Initialize the server using the RedisMixin
        # We need to call the mixin's __init__ which will start the server
        
        # Start the embedded server using sync client
        self._sync_client = SyncRedis(dbfilename=dbfilename, serverconfig=serverconfig or {})
        # Mark the sync client as managed by async to prevent shutdown issues
        self._sync_client._async_managed = True
        
        # Copy server-related attributes
        self.redis_dir = self._sync_client.redis_dir
        self.pidfile = self._sync_client.pidfile
        self.socket_file = self._sync_client.socket_file
        self.dbfilename = self._sync_client.dbfilename
        self.dbdir = self._sync_client.dbdir
        self.redis_configuration = self._sync_client.redis_configuration
        self.redis_configuration_filename = self._sync_client.redis_configuration_filename
        self.settingregistryfile = self._sync_client.settingregistryfile
        self.cleanupregistry = self._sync_client.cleanupregistry
        self.running = self._sync_client.running
        
        # Create the async Redis connection
        self._client = aioredis.Redis(
            unix_socket_path=self.socket_file,
            decode_responses=True,
            **kwargs
        )
        
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
        return False
    
    async def close(self):
        """Close the async connection and cleanup the server."""
        if '_client' in self.__dict__:
            # Note: redis.asyncio.Redis uses aclose() not close()
            await self._client.aclose()
        if '_sync_client' in self.__dict__:
            # Mark the sync client as managed by async to prevent it from attempting shutdown
            self._sync_client._async_managed = True
            self._sync_client._cleanup()
    
    def __getattr__(self, name):
        """
        Proxy attribute access to the underlying async Redis client.
        
        This allows AsyncRedis to act like a redis.asyncio.Redis instance
        for all Redis commands.
        """
        # Use object.__getattribute__ to avoid recursion
        try:
            client = object.__getattribute__(self, '_client')
        except AttributeError:
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}' "
                f"(client not initialized)"
            )
        
        # Now try to get the attribute from the client
        try:
            return getattr(client, name)
        except AttributeError:
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'"
            )
    
    @property
    def pid(self):
        """Get the Redis server process ID."""
        if '_sync_client' in self.__dict__:
            return self._sync_client.pid
        return None
    
    def _connection_count(self):
        """Get the number of connections to the Redis server."""
        if '_sync_client' in self.__dict__:
            return self._sync_client._connection_count()
        return 0


class AsyncStrictRedis(AsyncRedis):
    """
    Async version of StrictRedis for backwards compatibility.
    
    In modern redis-py, Redis and StrictRedis are equivalent.
    This class exists for API compatibility.
    """
    pass

# Copyright (c) 2024, FalkorDB
# Copyrights licensed under the New BSD License
# See the accompanying LICENSE.txt file for terms.
"""
Async FalkorDB client wrapper for redislite.

This module provides async versions of the FalkorDB client classes
that work with the embedded Redis + FalkorDB server.
"""
import asyncio
import json
from typing import Any, List, Dict, Optional

from .async_client import AsyncRedis


__all__ = ["AsyncFalkorDB", "AsyncGraph"]


class _SimpleResult:
    """
    Simple result wrapper for FalkorDB query results.
    
    This provides a basic interface for accessing query results
    when the full falkordb QueryResult is not available.
    """
    def __init__(self, result):
        """Initialize with raw result from Redis."""
        # Handle list results
        if isinstance(result, list):
            # First element is usually the result set if list is not empty
            self.result_set = result[0] if result and len(result) > 0 else []
        else:
            self.result_set = []
        self._raw = result


class AsyncGraph:
    """
    Async Graph class for executing Cypher queries asynchronously.
    
    This class provides async methods for interacting with FalkorDB graphs.
    
    Example:
        >>> import asyncio
        >>> from redislite.async_falkordb_client import AsyncFalkorDB
        >>> 
        >>> async def main():
        ...     db = AsyncFalkorDB('/tmp/falkordb.db')
        ...     g = db.select_graph('social')
        ...     
        ...     # Create nodes asynchronously
        ...     result = await g.query('CREATE (p:Person {name: "Alice", age: 30}) RETURN p')
        ...     
        ...     # Query asynchronously
        ...     result = await g.query('MATCH (p:Person) RETURN p.name, p.age')
        ...     for row in result.result_set:
        ...         print(row)
        ...     
        ...     await db.close()
        >>> 
        >>> asyncio.run(main())
    """
    
    def __init__(self, client: AsyncRedis, name: str):
        """
        Initialize an async graph.
        
        Args:
            client: The async Redis client instance
            name: The name of the graph
        """
        self.client = client
        self.name = name
    
    async def query(
        self,
        q: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None
    ):
        """
        Execute a Cypher query asynchronously.
        
        Args:
            q: The Cypher query string
            params: Optional query parameters
            timeout: Optional query timeout in milliseconds
            
        Returns:
            QueryResult: The query result
        """
        # Build the command
        command_args = [q]
        
        # Add parameters if provided
        if params:
            # Convert params to the format expected by FalkorDB
            command_args.append(json.dumps(params))
        
        # Add timeout if provided
        if timeout is not None:
            command_args.extend(['timeout', str(timeout)])
        
        # Execute the GRAPH.QUERY command
        result = await self.client.execute_command(
            'GRAPH.QUERY',
            self.name,
            *command_args
        )
        
        # Parse and return the result
        return self._parse_result(result)
    
    async def ro_query(
        self,
        q: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None
    ):
        """
        Execute a read-only Cypher query asynchronously.
        
        Args:
            q: The Cypher query string
            params: Optional query parameters
            timeout: Optional query timeout in milliseconds
            
        Returns:
            QueryResult: The query result
        """
        # Build the command
        command_args = [q]
        
        # Add parameters if provided
        if params:
            command_args.append(json.dumps(params))
        
        # Add timeout if provided
        if timeout is not None:
            command_args.extend(['timeout', str(timeout)])
        
        # Execute the GRAPH.RO_QUERY command
        result = await self.client.execute_command(
            'GRAPH.RO_QUERY',
            self.name,
            *command_args
        )
        
        # Parse and return the result
        return self._parse_result(result)
    
    async def delete(self):
        """
        Delete the graph asynchronously.
        
        Returns:
            The result of the delete operation
        """
        result = await self.client.execute_command('GRAPH.DELETE', self.name)
        return result
    
    async def copy(self, clone: str):
        """
        Create a copy of the graph asynchronously.
        
        Args:
            clone: The name for the copied graph
            
        Returns:
            AsyncGraph: A new AsyncGraph instance for the copied graph
        """
        await self.client.execute_command('GRAPH.COPY', self.name, clone)
        return AsyncGraph(self.client, clone)
    
    def _parse_result(self, raw_result):
        """
        Parse the raw result from Redis into a QueryResult.
        
        This is a simplified parser. In practice, you'd want to use
        the full FalkorDB result parser.
        
        Args:
            raw_result: The raw result from Redis
            
        Returns:
            A simple result object with result_set attribute
        """
        # Try to use falkordb's QueryResult if available (future enhancement)
        # For now, we use our simple result wrapper
        return _SimpleResult(raw_result)


class AsyncFalkorDB:
    """
    Async FalkorDB client for interacting with a FalkorDB-enabled Redis server.
    
    This class provides async operations for managing graphs and executing
    Cypher queries using the embedded Redis + FalkorDB server.
    
    Example:
        >>> import asyncio
        >>> from redislite.async_falkordb_client import AsyncFalkorDB
        >>> 
        >>> async def main():
        ...     # Create a FalkorDB instance (uses embedded Redis with FalkorDB)
        ...     db = AsyncFalkorDB('/tmp/falkordb.db')
        ...     
        ...     # Select a graph
        ...     g = db.select_graph('social')
        ...     
        ...     # Execute queries asynchronously
        ...     result = await g.query('CREATE (n:Person {name: "Alice"}) RETURN n')
        ...     
        ...     # List all graphs
        ...     graphs = await db.list_graphs()
        ...     print(graphs)
        ...     
        ...     # Clean up
        ...     await db.close()
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
        Create a new async FalkorDB instance using redislite.
        
        Args:
            dbfilename: Path to the database file (optional)
            serverconfig: Additional Redis server configuration (optional)
            **kwargs: Additional arguments passed to the async Redis client
        """
        self.client = AsyncRedis(
            dbfilename=dbfilename,
            serverconfig=serverconfig or {},
            **kwargs
        )
        self.connection = self.client
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
        return False
    
    def select_graph(self, name: str) -> AsyncGraph:
        """
        Select a graph by name.
        
        Args:
            name: The name of the graph
            
        Returns:
            AsyncGraph: An AsyncGraph instance for the specified graph
        """
        return AsyncGraph(self.client, name)
    
    async def list_graphs(self) -> List[str]:
        """
        List all graphs in the database asynchronously.
        
        Returns:
            List[str]: A list of graph names
        """
        try:
            result = await self.client.execute_command('GRAPH.LIST')
            return result if result else []
        except Exception as e:
            # If FalkorDB module is not loaded, the command will fail
            # We catch broadly here since redis errors can vary
            error_msg = str(e).lower()
            if 'unknown command' in error_msg or 'graph' in error_msg:
                return []
            # Re-raise unexpected errors
            raise
    
    async def close(self):
        """Close the connection and cleanup."""
        if 'client' in self.__dict__:
            await self.client.close()
    
    async def flushdb(self):
        """Flush the current database asynchronously."""
        return await self.client.flushdb()
    
    async def execute_command(self, *args, **kwargs):
        """
        Execute a Redis command asynchronously.
        
        Args:
            *args: Command and arguments
            **kwargs: Additional keyword arguments
            
        Returns:
            The command result
        """
        return await self.client.execute_command(*args, **kwargs)

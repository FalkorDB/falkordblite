# Copyright (c) 2024, FalkorDB
# Copyrights licensed under the New BSD License
# See the accompanying LICENSE.txt file for terms.
"""Async FalkorDB client wrapper for redislite."""
import importlib
from importlib import util as importlib_util
from pathlib import Path
import sys
from typing import Any, List, Optional

from .async_client import AsyncRedis

_PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _load_python_falkordb_asyncio():
    """Load the falkordb.asyncio module, avoiding the local falkordb.so file."""
    module_name = "falkordb.asyncio"
    
    # Check if already loaded
    existing = sys.modules.get(module_name)
    if existing and hasattr(existing, 'FalkorDB'):
        return existing
    
    # Temporarily filter out PROJECT_ROOT to avoid loading the local .so file
    original_sys_path = list(sys.path)
    try:
        sanitized = [
            entry for entry in original_sys_path
            if Path(entry or ".").resolve() != _PROJECT_ROOT
        ]
        sys.path[:] = sanitized
        module = importlib.import_module(module_name)
        return module
    except ImportError as e:
        raise ImportError(f"Unable to locate falkordb.asyncio: {e}")
    finally:
        sys.path[:] = original_sys_path


# Load the async classes from falkordb-py
BaseAsyncFalkorDB: Any
BaseAsyncGraph: Any
BaseQueryResult: Any

_falkordb_asyncio = _load_python_falkordb_asyncio()
BaseAsyncFalkorDB = _falkordb_asyncio.FalkorDB
# Import AsyncGraph from the graph submodule
from falkordb.asyncio.graph import AsyncGraph as BaseAsyncGraph
BaseQueryResult = _falkordb_asyncio.query_result.QueryResult

AsyncQueryResult = BaseQueryResult

__all__ = ["AsyncFalkorDB", "AsyncGraph", "AsyncQueryResult"]


class _EmbeddedAsyncGraphMixin:
    """Mixin that adapts falkordb-py AsyncGraph to the embedded client."""

    client: Any

    async def copy(self, clone: str):  # type: ignore[override]
        """Ensure copies return the embedded AsyncGraph subclass."""
        await BaseAsyncGraph.copy(self, clone)
        return AsyncGraph(self.client, clone)


class AsyncGraph(_EmbeddedAsyncGraphMixin, BaseAsyncGraph):
    """Async Graph implementation that reuses falkordb-py's full API surface."""

    def __init__(self, client, name: str):
        """Initialize async graph with client and name."""
        BaseAsyncGraph.__init__(self, client, name)


class _EmbeddedAsyncFalkorDBMixin:
    """Mixin that wires falkordb-py asyncio into the embedded Redis server."""

    def __init__(self, dbfilename: Optional[str] = None, serverconfig: Optional[dict] = None, **kwargs):
        """Create a new async FalkorDB instance using redislite."""
        self.client = AsyncRedis(
            dbfilename=dbfilename,
            serverconfig=serverconfig or {},
            **kwargs
        )
        self.connection = self.client
        # Note: execute_command and flushdb are available on AsyncRedis via proxying
        
    def select_graph(self, name: str) -> AsyncGraph:
        """Select a graph by name using the embedded AsyncGraph subclass."""
        return AsyncGraph(self.client, name)

    async def list_graphs(self) -> List[str]:
        """Return graph names, tolerating missing FalkorDB module."""
        try:
            result = await BaseAsyncFalkorDB.list_graphs(self)
            return result if result else []
        except Exception as e:
            # Check for specific FalkorDB module errors
            error_msg = str(e).lower()
            if 'unknown command' in error_msg or 'err unknown' in error_msg:
                # FalkorDB module not loaded
                return []
            # Re-raise unexpected errors
            raise


class AsyncFalkorDB(_EmbeddedAsyncFalkorDBMixin, BaseAsyncFalkorDB):
    """
    Async FalkorDB Class for interacting with a FalkorDB-enabled Redis server.

    This is a wrapper around redislite's AsyncRedis client that provides
    FalkorDB-specific async functionality for graph database operations.

    Usage example::
        from redislite.async_falkordb_client import AsyncFalkorDB

        # Create an async FalkorDB instance (uses embedded Redis with FalkorDB)
        async with AsyncFalkorDB('/tmp/falkordb.db') as db:
            # Select a graph
            g = db.select_graph('social')

            # Execute a query
            result = await g.query('CREATE (n:Person {name: "Alice"}) RETURN n')

            # Get the result
            for row in result.result_set:
                print(row)
    """

    async def close(self):
        """Close the connection and cleanup."""
        if hasattr(self, 'client'):
            await self.client.close()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
        return False

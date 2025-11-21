# Copyright (c) 2024, FalkorDB
# Copyrights licensed under the New BSD License
# See the accompanying LICENSE.txt file for terms.
"""
FalkorDB client wrapper for redislite

This module provides a FalkorDB-compatible API wrapper around the redislite client
to enable graph database operations using Cypher queries. Uses the official falkordb-py
library for API compatibility.
"""
from typing import Optional, List
from .client import Redis, StrictRedis

# Import the official falkordb Graph class
try:
    from falkordb import Graph as FalkorDBGraph
except ImportError:
    # Fallback if falkordb is not installed
    FalkorDBGraph = None


# Use the official falkordb.Graph class directly if available
if FalkorDBGraph is not None:
    class Graph(FalkorDBGraph):
        """
        Graph class that extends the official falkordb.Graph class.
        This provides full compatibility with the falkordb-py API while
        working with the embedded Redis server.
        
        All methods from falkordb.Graph are available, including:
        - query, ro_query: Execute Cypher queries
        - delete, copy: Graph management
        - slowlog, slowlog_reset: Performance monitoring
        - profile, explain: Query analysis
        - create_*_index, drop_*_index: Index operations
        - create_*_constraint, drop_*_constraint: Constraint operations
        - list_indices, list_constraints: Metadata queries
        - call_procedure: Execute stored procedures
        """
        pass
else:
    # Fallback implementation if falkordb is not installed
    class Graph:
        """
        Fallback Graph implementation when falkordb-py is not available.
        """
        def __init__(self, client, name: str):
            self._name = name
            self.client = client
            self.execute_command = client.execute_command
        
        @property
        def name(self) -> str:
            return self._name


class FalkorDB:
    """
    FalkorDB Class for interacting with a FalkorDB-enabled Redis server.

    This is a wrapper around redislite's Redis client that provides
    FalkorDB-specific functionality for graph database operations.

    Usage example::
        from redislite.falkordb_client import FalkorDB

        # Create a FalkorDB instance (uses embedded Redis with FalkorDB)
        db = FalkorDB('/tmp/falkordb.db')

        # Select a graph
        g = db.select_graph('social')

        # Execute a query
        result = g.query('CREATE (n:Person {name: "Alice"}) RETURN n')

        # Get the result
        for row in result.result_set:
            print(row)
    """

    def __init__(self, dbfilename=None, serverconfig=None, **kwargs):
        """
        Create a new FalkorDB instance using redislite.

        Args:
            dbfilename (str): Path to the database file (optional)
            serverconfig (dict): Additional Redis server configuration (optional)
            **kwargs: Additional arguments passed to the Redis client
        """
        # Create an embedded Redis instance with FalkorDB module loaded
        self.client = Redis(
            dbfilename=dbfilename,
            serverconfig=serverconfig or {},
            **kwargs
        )

    def select_graph(self, name: str) -> Graph:
        """
        Select a graph by name.

        Args:
            name (str): The name of the graph

        Returns:
            Graph: A Graph instance
        """
        return Graph(self.client, name)

    def list_graphs(self) -> List[str]:
        """
        List all graphs in the database.

        Returns:
            List[str]: List of graph names
        """
        try:
            result = self.client.execute_command("GRAPH.LIST")
            return result if result else []
        except Exception:
            return []

    def close(self):
        """Close the connection and cleanup."""
        if hasattr(self.client, '_cleanup'):
            self.client._cleanup()

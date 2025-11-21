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

from falkordb import Graph as FalkorDBGraph
from falkordb import FalkorDB as FalkorDBBase


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

class FalkorDB(FalkorDBBase):
    """
    FalkorDB Class for interacting with a FalkorDB-enabled embedded Redis server.
    
    This class extends the official falkordb.FalkorDB class to work with
    redislite's embedded Redis server while maintaining full API compatibility.
    
    All methods from falkordb.FalkorDB are available, including:
    - select_graph: Select a graph by name
    - list_graphs: List all graphs
    - config_get, config_set: Server configuration
    - from_url: Create from connection URL
    
    Usage example::
        from redislite.falkordb_client import FalkorDB
        
        # Create a FalkorDB instance (uses embedded Redis with FalkorDB)
        db = FalkorDB('/tmp/falkordb.db')
        
        # Select a graph
        g = db.select_graph('social')
        
        # Execute a query
        result = g.query('CREATE (n:Person {name: "Alice"}) RETURN n')
    """
    
    def __init__(self, dbfilename=None, serverconfig=None, **kwargs):
        """
        Create a new FalkorDB instance using redislite's embedded Redis.
        
        Args:
            dbfilename (str): Path to the database file (optional)
            serverconfig (dict): Additional Redis server configuration (optional)
            **kwargs: Additional arguments passed to the Redis client
        """
        # Create an embedded Redis instance with FalkorDB module loaded
        redis_client = Redis(
            dbfilename=dbfilename,
            serverconfig=serverconfig or {},
            **kwargs
        )
        
        # Set the connection attribute that FalkorDB base class expects
        self.connection = redis_client
        self.execute_command = redis_client.execute_command
        
        # Store reference to the client for cleanup
        self._redis_client = redis_client
    
    def select_graph(self, graph_id: str) -> Graph:
        """
        Selects a graph by creating a new Graph instance.
        
        This override ensures that our custom Graph class (which inherits from
        falkordb.Graph) is used instead of the base falkordb.Graph class.
        
        Args:
            graph_id (str): The identifier of the graph.
        
        Returns:
            Graph: A new Graph instance associated with the selected graph.
        """
        if not isinstance(graph_id, str) or graph_id == "":
            raise TypeError(
                f"Expected a string parameter, but received {type(graph_id)}."
            )
        
        return Graph(self, graph_id)
    
    def close(self):
        """Close the connection and cleanup."""
        if hasattr(self._redis_client, '_cleanup'):
            self._redis_client._cleanup()

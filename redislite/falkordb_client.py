# Copyright (c) 2024, FalkorDB
# Copyrights licensed under the New BSD License
# See the accompanying LICENSE.txt file for terms.
"""
FalkorDB client wrapper for redislite

This module provides a FalkorDB-compatible API wrapper around the redislite client
to enable graph database operations using Cypher queries.
"""
import json
from typing import Dict, Optional, List, Any
from .client import Redis, StrictRedis


class Graph:
    """
    Graph, collection of nodes and edges.
    Provides methods to execute Cypher queries against a FalkorDB graph.
    """

    def __init__(self, client, name: str):
        """
        Create a new graph.

        Args:
            client: The Redis client object.
            name (str): Graph ID/name
        """
        self._name = name
        self.client = client

    @property
    def name(self) -> str:
        """
        Get the graph name.

        Returns:
            str: The graph name.
        """
        return self._name

    def query(self, q: str, params: Optional[Dict[str, Any]] = None,
              timeout: Optional[int] = None):
        """
        Executes a Cypher query against the graph.

        Args:
            q (str): The Cypher query.
            params (dict): Query parameters (optional).
            timeout (int): Maximum query runtime in milliseconds (optional).

        Returns:
            QueryResult: Query result set.
        """
        query = q

        # Build query command
        command = ["GRAPH.QUERY", self.name, query]

        # Add parameters if provided
        if params:
            command.extend(["PARAMS", str(len(params) * 2)])
            for key, value in params.items():
                command.extend([key, json.dumps(value)])

        # Include timeout if specified
        if isinstance(timeout, int):
            command.extend(["TIMEOUT", timeout])
        elif timeout is not None:
            raise Exception("Timeout argument must be a positive integer")

        # Add compact flag at the end
        command.append("--compact")
        
        # Execute query
        response = self.client.execute_command(*command)
        return QueryResult(response)

    def ro_query(self, q: str, params: Optional[Dict[str, Any]] = None,
                 timeout: Optional[int] = None):
        """
        Executes a read-only Cypher query against the graph.

        Args:
            q (str): The Cypher query.
            params (dict): Query parameters (optional).
            timeout (int): Maximum query runtime in milliseconds (optional).

        Returns:
            QueryResult: Query result set.
        """
        query = q

        # Build query command
        command = ["GRAPH.RO_QUERY", self.name, query]

        # Add parameters if provided
        if params:
            command.extend(["PARAMS", str(len(params) * 2)])
            for key, value in params.items():
                command.extend([key, json.dumps(value)])

        # Include timeout if specified
        if isinstance(timeout, int):
            command.extend(["TIMEOUT", timeout])
        elif timeout is not None:
            raise Exception("Timeout argument must be a positive integer")

        # Add compact flag at the end
        command.append("--compact")
        
        # Execute query
        response = self.client.execute_command(*command)
        return QueryResult(response)

    def delete(self) -> None:
        """
        Deletes the graph.

        Returns:
            None
        """
        return self.client.execute_command("GRAPH.DELETE", self._name)

    def copy(self, clone: str):
        """
        Creates a copy of the graph.

        Args:
            clone (str): Name of cloned graph

        Returns:
            Graph: The cloned graph
        """
        self.client.execute_command("GRAPH.COPY", self.name, clone)
        return Graph(self.client, clone)

    def slowlog(self):
        """
        Get a list containing up to 10 of the slowest queries issued
        against the graph.

        Returns:
            List: List of slow log entries.
        """
        return self.client.execute_command("GRAPH.SLOWLOG", self._name)


class QueryResult:
    """
    Represents the result of a graph query.
    """

    def __init__(self, response):
        """
        Initialize query result.

        Args:
            response: Raw response from Redis/FalkorDB
        """
        self._raw_response = response
        self._parse_response(response)

    def _parse_response(self, response):
        """
        Parse the raw response from FalkorDB.

        Args:
            response: Raw response from Redis/FalkorDB
        """
        # FalkorDB returns results in a specific format
        # [result_set, statistics]
        if isinstance(response, list) and len(response) >= 2:
            self.result_set = response[0] if response[0] else []
            self._statistics = response[1] if len(response) > 1 else []
        else:
            self.result_set = []
            self._statistics = []

    @property
    def statistics(self):
        """Get query statistics."""
        return self._statistics


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

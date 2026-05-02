# Copyright (c) 2024, FalkorDB
# Copyrights licensed under the New BSD License
# See the accompanying LICENSE.txt file for terms.
"""FalkorDB client wrapper for redislite."""
import importlib
from importlib import util as importlib_util
from pathlib import Path
import sys
from typing import Any, List

from .client import Redis
from .client import StrictRedis as _StrictRedis

_PROJECT_ROOT = Path(__file__).resolve().parents[1]

# `falkordb-py` ships as a pure Python package.  This workspace bundles a
# `falkordb.so` artifact for the embedded server which would otherwise shadow
# the Python driver on the import path.  Load the Python sources explicitly so
# we always expose the rich driver API the issue requires.
def _load_python_falkordb():
    module_name = "falkordb"
    existing = sys.modules.get(module_name)
    if existing and isinstance(getattr(existing, "__file__", None), str):
        file_path = getattr(existing, "__file__", "")
        if isinstance(file_path, str) and file_path.endswith("__init__.py"):
            return existing

    original_sys_path = list(sys.path)
    try:
        sanitized = [
            entry for entry in original_sys_path
            if Path(entry or ".").resolve() != _PROJECT_ROOT
        ]
        sys.path[:] = sanitized
        module = importlib.import_module(module_name)
        file_path = getattr(module, "__file__", "")
        if isinstance(file_path, str) and file_path.endswith("__init__.py"):
            return module
    except ImportError:
        pass
    finally:
        sys.path[:] = original_sys_path

    for entry in list(sys.path):
        candidate = Path(entry) / module_name / "__init__.py"
        if candidate.is_file():
            spec = importlib_util.spec_from_file_location(
                module_name,
                candidate,
                submodule_search_locations=[str(candidate.parent)],
            )
            if spec and spec.loader:
                module = importlib_util.module_from_spec(spec)
                spec.loader.exec_module(module)
                sys.modules[module_name] = module
                return module

    raise ImportError("Unable to locate the Python implementation of falkordb")


BaseFalkorDB: Any
BaseGraph: Any
BaseQueryResult: Any

_falkordb = _load_python_falkordb()
BaseFalkorDB = _falkordb.FalkorDB
BaseGraph = _falkordb.Graph
BaseQueryResult = _falkordb.QueryResult

StrictRedis = _StrictRedis
QueryResult = BaseQueryResult

__all__ = ["FalkorDB", "Graph", "QueryResult", "Redis", "StrictRedis"]


class _EmbeddedGraphMixin:
    """Mixin that adapts falkordb-py Graph to the embedded client."""

    client: Any

    def copy(self, clone: str):  # type: ignore[override]
        """Ensure copies return the embedded Graph subclass."""
        BaseGraph.copy(self, clone)
        return Graph(self.client, clone)


class Graph(_EmbeddedGraphMixin, BaseGraph):
    """Graph implementation that reuses falkordb-py's full API surface."""

    def __init__(self, client, name: str):  # noqa: D401 - inherit docstring
        BaseGraph.__init__(self, client, name)


class _EmbeddedFalkorDBMixin:
    """Mixin that wires falkordb-py into the embedded Redis server."""

    def __init__(self, dbfilename=None, serverconfig=None, **kwargs):
        """Create a new FalkorDB instance using redislite."""
        self.client = Redis(
            dbfilename=dbfilename,
            serverconfig=serverconfig or {},
            decode_responses=True,
            **kwargs
        )
        self.connection = self.client
        self.execute_command = self.client.execute_command
        self.flushdb = self.client.flushdb

    def select_graph(self, name: str) -> Graph:
        """Select a graph by name using the embedded Graph subclass."""
        return Graph(self.client, name)

    def list_graphs(self) -> List[str]:
        """Return graph names, tolerating missing FalkorDB module."""
        try:
            result = BaseFalkorDB.list_graphs(self)
            return result if result else []
        except Exception:
            return []


class FalkorDB(_EmbeddedFalkorDBMixin, BaseFalkorDB):
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

    def close(self):
        """Close the connection and cleanup."""
        if hasattr(self.client, '_cleanup'):
            self.client._cleanup()

# Copyright (c) 2024, FalkorDB
# Copyrights licensed under the New BSD License
# See the accompanying LICENSE.txt file for terms.
"""
Tests for FalkorDB client functionality.
"""
import os
import tempfile
import unittest
from unittest.mock import Mock
from redislite.falkordb_client import FalkorDB, Graph


class TestFalkorDBClient(unittest.TestCase):
    """Test FalkorDB client functionality"""

    def test_graph_inheritance(self):
        """Test that Graph class inherits from falkordb.Graph"""
        try:
            import falkordb
            # Verify that our Graph class inherits from falkordb.Graph
            self.assertTrue(issubclass(Graph, falkordb.Graph))
            
            # Verify that all key methods from falkordb.Graph are available
            expected_methods = [
                'query', 'ro_query', 'delete', 'copy', 'slowlog', 'slowlog_reset',
                'profile', 'explain', 'call_procedure',
                'create_node_range_index', 'create_node_fulltext_index', 'create_node_vector_index',
                'create_edge_range_index', 'create_edge_fulltext_index', 'create_edge_vector_index',
                'drop_node_range_index', 'drop_node_fulltext_index', 'drop_node_vector_index',
                'drop_edge_range_index', 'drop_edge_fulltext_index', 'drop_edge_vector_index',
                'create_node_unique_constraint', 'create_node_mandatory_constraint',
                'create_edge_unique_constraint', 'create_edge_mandatory_constraint',
                'drop_node_unique_constraint', 'drop_node_mandatory_constraint',
                'drop_edge_unique_constraint', 'drop_edge_mandatory_constraint',
                'list_indices', 'list_constraints'
            ]
            
            for method_name in expected_methods:
                self.assertTrue(hasattr(Graph, method_name), 
                              f"Graph class should have method: {method_name}")
        except ImportError:
            self.skipTest("falkordb package not installed")

    def test_graph_instance_creation(self):
        """Test that we can create Graph instances with the new inheritance"""
        try:
            import falkordb
            # Create a mock client
            mock_client = Mock()
            mock_client.execute_command = Mock(return_value=[[['node_data']], ['stats']])
            
            # Create a Graph instance
            graph = Graph(mock_client, 'test_graph')
            
            # Verify basic properties
            self.assertEqual(graph.name, 'test_graph')
            self.assertEqual(graph.client, mock_client)
            self.assertTrue(hasattr(graph, 'execute_command'))
            
            # Verify it's an instance of both our Graph and falkordb.Graph
            self.assertIsInstance(graph, Graph)
            self.assertIsInstance(graph, falkordb.Graph)
        except ImportError:
            self.skipTest("falkordb package not installed")

    def test_falkordb_class_inheritance(self):
        """Test that FalkorDB class inherits from falkordb.FalkorDB"""
        try:
            import falkordb
            # Verify that our FalkorDB class inherits from falkordb.FalkorDB
            self.assertTrue(issubclass(FalkorDB, falkordb.FalkorDB))
            
            # Verify that all key methods from falkordb.FalkorDB are available
            expected_methods = [
                'select_graph', 'list_graphs', 'config_get', 'config_set', 'from_url'
            ]
            
            for method_name in expected_methods:
                self.assertTrue(hasattr(FalkorDB, method_name), 
                              f"FalkorDB class should have method: {method_name}")
        except ImportError:
            self.skipTest("falkordb package not installed")

    def test_falkordb_creation(self):
        """Test that we can create a FalkorDB instance"""
        temp_dir = tempfile.mkdtemp()
        db_file = os.path.join(temp_dir, 'falkordb.db')
        
        try:
            db = FalkorDB(dbfilename=db_file)
            self.assertIsNotNone(db)
            self.assertIsNotNone(db.client)
            db.close()
        finally:
            # Cleanup
            if os.path.exists(temp_dir):
                import shutil
                shutil.rmtree(temp_dir)

    def test_select_graph(self):
        """Test that we can select a graph"""
        temp_dir = tempfile.mkdtemp()
        db_file = os.path.join(temp_dir, 'falkordb.db')
        
        try:
            db = FalkorDB(dbfilename=db_file)
            graph = db.select_graph('test_graph')
            self.assertIsNotNone(graph)
            self.assertEqual(graph.name, 'test_graph')
            db.close()
        finally:
            # Cleanup
            if os.path.exists(temp_dir):
                import shutil
                shutil.rmtree(temp_dir)

    def test_simple_query(self):
        """Test executing a simple Cypher query"""
        temp_dir = tempfile.mkdtemp()
        db_file = os.path.join(temp_dir, 'falkordb.db')
        
        try:
            db = FalkorDB(dbfilename=db_file)
            graph = db.select_graph('social')
            
            # Create a simple node
            result = graph.query('CREATE (n:Person {name: "Alice"}) RETURN n')
            self.assertIsNotNone(result)
            
            # Query the node back
            result = graph.query('MATCH (n:Person) RETURN n')
            self.assertIsNotNone(result)
            self.assertIsNotNone(result.result_set)
            
            # Clean up
            graph.delete()
            db.close()
        except Exception as e:
            # If FalkorDB module is not loaded, skip this test
            if 'unknown command' in str(e).lower() or 'graph.query' in str(e).lower():
                self.skipTest(f"FalkorDB module not loaded: {e}")
            else:
                raise
        finally:
            # Cleanup
            if os.path.exists(temp_dir):
                import shutil
                shutil.rmtree(temp_dir)


if __name__ == '__main__':
    unittest.main()

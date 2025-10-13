# Copyright (c) 2024, FalkorDB
# Copyrights licensed under the New BSD License
# See the accompanying LICENSE.txt file for terms.
"""
Tests for FalkorDB client functionality.
"""
import os
import tempfile
import unittest
from redislite.falkordb_client import FalkorDB


class TestFalkorDBClient(unittest.TestCase):
    """Test FalkorDB client functionality"""

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

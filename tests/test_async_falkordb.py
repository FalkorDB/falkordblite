# Copyright (c) 2024, FalkorDB
# Copyrights licensed under the New BSD License
# See the accompanying LICENSE.txt file for terms.
"""
Tests for async FalkorDB client functionality.
"""
import asyncio
import os
import shutil
import tempfile
import unittest
from redislite.async_falkordb_client import AsyncFalkorDB
from redislite.async_client import AsyncRedis


class TestAsyncFalkorDBClient(unittest.TestCase):
    """Test async FalkorDB client functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_file = os.path.join(self.temp_dir, 'falkordb.db')

    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_async_falkordb_creation(self):
        """Test that we can create an AsyncFalkorDB instance"""
        async def run_test():
            db = AsyncFalkorDB(dbfilename=self.db_file)
            self.assertIsNotNone(db)
            self.assertIsNotNone(db.client)
            await db.close()
        
        asyncio.run(run_test())

    def test_async_select_graph(self):
        """Test that we can select a graph asynchronously"""
        async def run_test():
            db = AsyncFalkorDB(dbfilename=self.db_file)
            graph = db.select_graph('test_graph')
            self.assertIsNotNone(graph)
            self.assertEqual(graph.name, 'test_graph')
            await db.close()
        
        asyncio.run(run_test())

    def test_async_simple_query(self):
        """Test executing a simple Cypher query asynchronously"""
        async def run_test():
            try:
                db = AsyncFalkorDB(dbfilename=self.db_file)
                graph = db.select_graph('social')
                
                # Create a simple node with parameterized query
                result = await graph.query(
                    'CREATE (n:Person {name: $name}) RETURN n',
                    params={'name': 'Alice'}
                )
                self.assertIsNotNone(result)
                
                # Query the node back
                result = await graph.query('MATCH (n:Person) RETURN n')
                self.assertIsNotNone(result)
                self.assertIsNotNone(result.result_set)
                
                # Clean up
                await graph.delete()
                await db.close()
            except Exception as e:
                # If FalkorDB module is not loaded, skip this test
                if 'unknown command' in str(e).lower() or 'graph.query' in str(e).lower():
                    self.skipTest(f"FalkorDB module not loaded: {e}")
                else:
                    raise
        
        asyncio.run(run_test())

    def test_async_context_manager(self):
        """Test using AsyncFalkorDB as a context manager"""
        async def run_test():
            async with AsyncFalkorDB(dbfilename=self.db_file) as db:
                graph = db.select_graph('test')
                self.assertIsNotNone(graph)
            # Connection should be closed automatically
        
        asyncio.run(run_test())

    def test_async_redis_basic_operations(self):
        """Test basic async Redis operations"""
        async def run_test():
            redis_conn = AsyncRedis(dbfilename=self.db_file)
            
            # Test set and get
            await redis_conn.set('key', 'value')
            value = await redis_conn.get('key')
            self.assertEqual(value, 'value')
            
            # Test delete
            await redis_conn.delete('key')
            value = await redis_conn.get('key')
            self.assertIsNone(value)
            
            await redis_conn.close()
        
        asyncio.run(run_test())

    def test_async_list_graphs(self):
        """Test listing graphs asynchronously"""
        async def run_test():
            try:
                db = AsyncFalkorDB(dbfilename=self.db_file)
                
                # List graphs (should be empty or return a list)
                graphs = await db.list_graphs()
                self.assertIsInstance(graphs, list)
                
                await db.close()
            except Exception as e:
                # If FalkorDB module is not loaded, skip this test
                if 'unknown command' in str(e).lower():
                    self.skipTest(f"FalkorDB module not loaded: {e}")
                else:
                    raise
        
        asyncio.run(run_test())


if __name__ == '__main__':
    unittest.main()

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

    def test_async_udf_load_and_call(self):
        """Test loading and calling a User Defined Function (UDF) asynchronously"""
        async def run_test():
            try:
                db = AsyncFalkorDB(dbfilename=self.db_file)
                
                # JavaScript UDF that uppercases odd-indexed characters
                lib_name = "AsyncStringUtils"
                udf_script = """
                function UpperCaseOdd(s) {
                    return s.split('')
                        .map((char, i) => (i % 2 !== 0 ? char.toUpperCase() : char))
                        .join('');
                }
                falkor.register('UpperCaseOdd', UpperCaseOdd);
                """
                
                # Load the UDF library
                await db.udf_load(lib_name, udf_script)
                
                # Verify UDF was loaded by listing UDFs
                udf_list = await db.udf_list()
                self.assertIn(lib_name, udf_list)
                
                # Use the UDF in a query
                graph = db.select_graph('test_async_udf')
                result = await graph.query(f"RETURN {lib_name}.UpperCaseOdd('abcdef') AS result")
                self.assertIsNotNone(result.result_set)
                self.assertEqual(len(result.result_set), 1)
                self.assertEqual(result.result_set[0][0], 'aBcDeF')
                
                # Clean up
                await graph.delete()
                await db.udf_delete(lib_name)
                await db.close()
            except Exception as e:
                # If FalkorDB module is not loaded or UDF not supported, skip this test
                if any(keyword in str(e).lower() for keyword in ['unknown command', 'graph.query', 'udf']):
                    self.skipTest(f"FalkorDB UDF not supported: {e}")
                else:
                    raise
        
        asyncio.run(run_test())

    def test_async_udf_with_graph_query(self):
        """Test using UDF in conjunction with graph queries asynchronously"""
        async def run_test():
            try:
                db = AsyncFalkorDB(dbfilename=self.db_file)
                
                # Load a UDF that formats names
                lib_name = "AsyncNameFormatter"
                udf_script = """
                function titleCase(s) {
                    return s.charAt(0).toUpperCase() + s.slice(1).toLowerCase();
                }
                falkor.register('titleCase', titleCase);
                """
                await db.udf_load(lib_name, udf_script)
                
                # Create graph with data
                graph = db.select_graph('async_people')
                await graph.query('CREATE (p:Person {name: "alice"})')
                await graph.query('CREATE (p:Person {name: "BOB"})')
                await graph.query('CREATE (p:Person {name: "cArOl"})')
                
                # Use UDF to format names in query
                result = await graph.query(
                    f"MATCH (p:Person) RETURN {lib_name}.titleCase(p.name) AS formatted_name ORDER BY formatted_name"
                )
                
                self.assertEqual(len(result.result_set), 3)
                self.assertEqual(result.result_set[0][0], 'Alice')
                self.assertEqual(result.result_set[1][0], 'Bob')
                self.assertEqual(result.result_set[2][0], 'Carol')
                
                # Clean up
                await graph.delete()
                await db.udf_delete(lib_name)
                await db.close()
            except Exception as e:
                # If FalkorDB module is not loaded or UDF not supported, skip this test
                if any(keyword in str(e).lower() for keyword in ['unknown command', 'graph.query', 'udf']):
                    self.skipTest(f"FalkorDB UDF not supported: {e}")
                else:
                    raise
        
        asyncio.run(run_test())

    def test_async_udf_list_and_delete(self):
        """Test listing and deleting UDFs asynchronously"""
        async def run_test():
            try:
                db = AsyncFalkorDB(dbfilename=self.db_file)
                
                # Load multiple UDF libraries
                lib1 = "AsyncLib1"
                lib2 = "AsyncLib2"
                
                udf_script1 = """
                function func1() { return "lib1"; }
                falkor.register('func1', func1);
                """
                udf_script2 = """
                function func2() { return "lib2"; }
                falkor.register('func2', func2);
                """
                
                await db.udf_load(lib1, udf_script1)
                await db.udf_load(lib2, udf_script2)
                
                # List UDFs - both should be present
                udf_list = await db.udf_list()
                self.assertIn(lib1, udf_list)
                self.assertIn(lib2, udf_list)
                
                # Delete one UDF
                await db.udf_delete(lib1)
                
                # Verify only lib2 remains
                udf_list = await db.udf_list()
                self.assertNotIn(lib1, udf_list)
                self.assertIn(lib2, udf_list)
                
                # Clean up
                await db.udf_delete(lib2)
                await db.close()
            except Exception as e:
                # If FalkorDB module is not loaded or UDF not supported, skip this test
                if any(keyword in str(e).lower() for keyword in ['unknown command', 'udf']):
                    self.skipTest(f"FalkorDB UDF not supported: {e}")
                else:
                    raise
        
        asyncio.run(run_test())


if __name__ == '__main__':
    unittest.main()

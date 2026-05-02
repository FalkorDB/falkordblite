# Copyright (c) 2024, FalkorDB
# Copyrights licensed under the New BSD License
# See the accompanying LICENSE.txt file for terms.
"""
Tests for FalkorDB client functionality.
"""
import os
import tempfile
import unittest
import shutil
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

    def test_udf_load_and_call(self):
        """Test loading and calling a User Defined Function (UDF)"""
        temp_dir = tempfile.mkdtemp()
        db_file = os.path.join(temp_dir, 'falkordb.db')
        
        try:
            db = FalkorDB(dbfilename=db_file)
            
            # JavaScript UDF that uppercases odd-indexed characters
            lib_name = "StringUtils"
            udf_script = """
            function UpperCaseOdd(s) {
                return s.split('')
                    .map((char, i) => (i % 2 !== 0 ? char.toUpperCase() : char))
                    .join('');
            }
            falkor.register('UpperCaseOdd', UpperCaseOdd);
            """
            
            # Load the UDF library
            db.udf_load(lib_name, udf_script)
            
            # Verify UDF was loaded by listing UDFs
            udf_list = db.udf_list()
            # udf_list returns format: [['library_name', '<name>', 'functions', [<func_list>]], ...]
            lib_names = [udf[1] for udf in udf_list if len(udf) > 1 and udf[0] == 'library_name']
            self.assertIn(lib_name, lib_names)
            
            # Use the UDF in a query
            graph = db.select_graph('test_udf')
            result = graph.query(f"RETURN {lib_name}.UpperCaseOdd('abcdef') AS result")
            self.assertIsNotNone(result.result_set)
            self.assertEqual(len(result.result_set), 1)
            self.assertEqual(result.result_set[0][0], 'aBcDeF')
            
            # Clean up
            graph.delete()
            db.udf_delete(lib_name)
            db.close()
        except Exception as e:
            # If FalkorDB module is not loaded or UDF not supported, skip this test
            if any(keyword in str(e).lower() for keyword in ['unknown command', 'graph.query', 'udf']):
                self.skipTest(f"FalkorDB UDF not supported: {e}")
            else:
                raise
        finally:
            # Cleanup
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def test_udf_multiple_functions(self):
        """Test loading a UDF library with multiple functions"""
        temp_dir = tempfile.mkdtemp()
        db_file = os.path.join(temp_dir, 'falkordb.db')
        
        try:
            db = FalkorDB(dbfilename=db_file)
            
            # JavaScript UDF library with multiple functions
            lib_name = "MathUtils"
            udf_script = """
            function add(a, b) {
                return a + b;
            }
            function multiply(a, b) {
                return a * b;
            }
            function square(x) {
                return x * x;
            }
            falkor.register('add', add);
            falkor.register('multiply', multiply);
            falkor.register('square', square);
            """
            
            # Load the UDF library
            db.udf_load(lib_name, udf_script)
            
            # Test each function
            graph = db.select_graph('test_math')
            
            # Test add
            result = graph.query(f"RETURN {lib_name}.add(5, 3) AS result")
            self.assertEqual(result.result_set[0][0], 8)
            
            # Test multiply
            result = graph.query(f"RETURN {lib_name}.multiply(4, 7) AS result")
            self.assertEqual(result.result_set[0][0], 28)
            
            # Test square
            result = graph.query(f"RETURN {lib_name}.square(6) AS result")
            self.assertEqual(result.result_set[0][0], 36)
            
            # Clean up
            graph.delete()
            db.udf_delete(lib_name)
            db.close()
        except Exception as e:
            # If FalkorDB module is not loaded or UDF not supported, skip this test
            if any(keyword in str(e).lower() for keyword in ['unknown command', 'graph.query', 'udf']):
                self.skipTest(f"FalkorDB UDF not supported: {e}")
            else:
                raise
        finally:
            # Cleanup
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def test_udf_with_graph_query(self):
        """Test using UDF in conjunction with graph queries"""
        temp_dir = tempfile.mkdtemp()
        db_file = os.path.join(temp_dir, 'falkordb.db')
        
        try:
            db = FalkorDB(dbfilename=db_file)
            
            # Load a UDF that formats names
            lib_name = "NameFormatter"
            udf_script = """
            function titleCase(s) {
                return s.charAt(0).toUpperCase() + s.slice(1).toLowerCase();
            }
            falkor.register('titleCase', titleCase);
            """
            db.udf_load(lib_name, udf_script)
            
            # Create graph with data
            graph = db.select_graph('people')
            graph.query('CREATE (p:Person {name: "alice"})')
            graph.query('CREATE (p:Person {name: "BOB"})')
            graph.query('CREATE (p:Person {name: "cArOl"})')
            
            # Use UDF to format names in query
            result = graph.query(
                f"MATCH (p:Person) RETURN {lib_name}.titleCase(p.name) AS formatted_name ORDER BY formatted_name"
            )
            
            self.assertEqual(len(result.result_set), 3)
            self.assertEqual(result.result_set[0][0], 'Alice')
            self.assertEqual(result.result_set[1][0], 'Bob')
            self.assertEqual(result.result_set[2][0], 'Carol')
            
            # Clean up
            graph.delete()
            db.udf_delete(lib_name)
            db.close()
        except Exception as e:
            # If FalkorDB module is not loaded or UDF not supported, skip this test
            if any(keyword in str(e).lower() for keyword in ['unknown command', 'graph.query', 'udf']):
                self.skipTest(f"FalkorDB UDF not supported: {e}")
            else:
                raise
        finally:
            # Cleanup
            if os.path.exists(temp_dir):
                import shutil
                shutil.rmtree(temp_dir)

    def test_udf_list_and_delete(self):
        """Test listing and deleting UDFs"""
        temp_dir = tempfile.mkdtemp()
        db_file = os.path.join(temp_dir, 'falkordb.db')
        
        try:
            db = FalkorDB(dbfilename=db_file)
            
            # Load multiple UDF libraries
            lib1 = "Lib1"
            lib2 = "Lib2"
            
            udf_script1 = """
            function func1() { return "lib1"; }
            falkor.register('func1', func1);
            """
            udf_script2 = """
            function func2() { return "lib2"; }
            falkor.register('func2', func2);
            """
            
            db.udf_load(lib1, udf_script1)
            db.udf_load(lib2, udf_script2)
            
            # List UDFs - both should be present
            udf_list = db.udf_list()
            # udf_list returns format: [['library_name', '<name>', 'functions', [<func_list>]], ...]
            lib_names = [udf[1] for udf in udf_list if len(udf) > 1 and udf[0] == 'library_name']
            self.assertIn(lib1, lib_names)
            self.assertIn(lib2, lib_names)
            
            # Delete one UDF
            db.udf_delete(lib1)
            
            # Verify only lib2 remains
            udf_list = db.udf_list()
            lib_names = [udf[1] for udf in udf_list if len(udf) > 1 and udf[0] == 'library_name']
            self.assertNotIn(lib1, lib_names)
            self.assertIn(lib2, lib_names)
            
            # Clean up
            db.udf_delete(lib2)
            db.close()
        except Exception as e:
            # If FalkorDB module is not loaded or UDF not supported, skip this test
            if any(keyword in str(e).lower() for keyword in ['unknown command', 'udf']):
                self.skipTest(f"FalkorDB UDF not supported: {e}")
            else:
                raise
        finally:
            # Cleanup
            if os.path.exists(temp_dir):
                import shutil
                shutil.rmtree(temp_dir)


if __name__ == '__main__':
    unittest.main()

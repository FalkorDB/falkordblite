#!/usr/bin/env python3
"""
Simple verification script to test FalkorDBLite installation
"""

import sys

def test_import():
    """Test that the package can be imported"""
    print("Testing imports...")
    try:
        from redislite.falkordb_client import FalkorDB
        print("✓ Successfully imported FalkorDB")
        return True
    except ImportError as e:
        print(f"✗ Failed to import FalkorDB: {e}")
        return False

def test_basic_operations():
    """Test basic FalkorDB operations"""
    print("\nTesting basic operations...")
    try:
        from redislite.falkordb_client import FalkorDB
        
        # Create instance
        db = FalkorDB()
        print("✓ Created FalkorDB instance")
        
        # Select graph
        g = db.select_graph('test')
        print("✓ Selected graph")
        
        # Create a node
        result = g.query('CREATE (n:Test {name: "verification"}) RETURN n')
        if result and result.result_set and len(result.result_set) > 0:
            print("✓ Created test node")
        else:
            print("✗ Failed to create test node")
            return False
        
        # Query the node
        result = g.query('MATCH (n:Test) RETURN n.name')
        if result.result_set:
            print(f"✓ Retrieved test node: {result.result_set[0]}")
        
        # Clean up
        g.delete()
        print("✓ Cleaned up test graph")
        
        return True
        
    except Exception as e:
        print(f"✗ Basic operations failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("="*50)
    print("FalkorDBLite Installation Verification")
    print("="*50)
    
    tests_passed = 0
    tests_total = 2
    
    if test_import():
        tests_passed += 1
    
    if test_basic_operations():
        tests_passed += 1
    
    print("\n" + "="*50)
    if tests_passed == tests_total:
        print(f"✓ All tests passed ({tests_passed}/{tests_total})")
        print("="*50)
        return 0
    else:
        print(f"✗ Some tests failed ({tests_passed}/{tests_total})")
        print("="*50)
        return 1

if __name__ == '__main__':
    sys.exit(main())

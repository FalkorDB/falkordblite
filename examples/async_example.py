#!/usr/bin/env python3
"""
Example script demonstrating the async API for FalkorDBLite.

This script shows how to use the async versions of FalkorDB and Redis clients.
"""
import asyncio
import sys
import os

# Add the project root to path for development
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from redislite.async_falkordb_client import AsyncFalkorDB
from redislite.async_client import AsyncRedis


async def demo_async_redis():
    """Demonstrate async Redis operations."""
    print("\n" + "=" * 60)
    print("Async Redis Example")
    print("=" * 60)
    
    # Create an async Redis connection
    redis_conn = AsyncRedis('/tmp/async_redis_demo.db')
    
    try:
        # Async set and get
        print("\n1. Setting key-value pairs...")
        await redis_conn.set('name', 'FalkorDB')
        await redis_conn.set('type', 'Graph Database')
        
        print("2. Getting values...")
        name = await redis_conn.get('name')
        db_type = await redis_conn.get('type')
        print(f"   Name: {name.decode()}")
        print(f"   Type: {db_type.decode()}")
        
        # Multiple operations concurrently
        print("\n3. Setting multiple keys concurrently...")
        await asyncio.gather(
            redis_conn.set('key1', 'value1'),
            redis_conn.set('key2', 'value2'),
            redis_conn.set('key3', 'value3'),
        )
        
        # Get all keys
        keys = await redis_conn.keys()
        print(f"   Total keys: {len(keys)}")
        print(f"   Keys: {[k.decode() for k in keys]}")
        
    finally:
        await redis_conn.close()
        print("\n✓ Redis connection closed")


async def demo_async_falkordb():
    """Demonstrate async FalkorDB graph operations."""
    print("\n" + "=" * 60)
    print("Async FalkorDB Example")
    print("=" * 60)
    
    # Create an async FalkorDB instance
    db = AsyncFalkorDB('/tmp/async_falkordb_demo.db')
    
    try:
        # Select a graph
        print("\n1. Creating a social graph...")
        g = db.select_graph('social')
        
        # Create nodes asynchronously using parameterized queries
        print("2. Creating person nodes...")
        await g.query(
            'CREATE (p:Person {name: $name, age: $age})',
            params={'name': 'Alice', 'age': 30}
        )
        await g.query(
            'CREATE (p:Person {name: $name, age: $age})',
            params={'name': 'Bob', 'age': 25}
        )
        await g.query(
            'CREATE (p:Person {name: $name, age: $age})',
            params={'name': 'Carol', 'age': 28}
        )
        
        # Create relationships using parameterized queries
        print("3. Creating relationships...")
        await g.query(
            '''
            MATCH (a:Person {name: $name_a}), (b:Person {name: $name_b})
            CREATE (a)-[:KNOWS]->(b)
            ''',
            params={'name_a': 'Alice', 'name_b': 'Bob'}
        )
        await g.query(
            '''
            MATCH (b:Person {name: $name_b}), (c:Person {name: $name_c})
            CREATE (b)-[:KNOWS]->(c)
            ''',
            params={'name_b': 'Bob', 'name_c': 'Carol'}
        )
        
        # Query the graph
        print("\n4. Querying all people:")
        result = await g.query('MATCH (p:Person) RETURN p.name, p.age ORDER BY p.name')
        for row in result.result_set:
            print(f"   - {row[0]}, age {row[1]}")
        
        # Query relationships
        print("\n5. Querying relationships:")
        result = await g.ro_query('''
            MATCH (p:Person)-[:KNOWS]->(f:Person)
            RETURN p.name, f.name
        ''')
        for row in result.result_set:
            print(f"   - {row[0]} knows {row[1]}")
        
        # List all graphs
        print("\n6. Listing all graphs:")
        graphs = await db.list_graphs()
        for graph_name in graphs:
            print(f"   - {graph_name}")
        
        # Clean up
        print("\n7. Cleaning up...")
        await g.delete()
        
    except Exception as e:
        if 'unknown command' in str(e).lower() or 'graph.query' in str(e).lower():
            print(f"\n⚠ FalkorDB module not loaded: {e}")
            print("   This is expected if the project hasn't been built yet.")
        else:
            raise
    finally:
        await db.close()
        print("✓ FalkorDB connection closed")


async def main():
    """Run all async examples."""
    print("\n" + "=" * 60)
    print("FalkorDBLite Async API Examples")
    print("=" * 60)
    
    # Run Redis example
    await demo_async_redis()
    
    # Run FalkorDB example
    await demo_async_falkordb()
    
    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60 + "\n")


if __name__ == '__main__':
    asyncio.run(main())

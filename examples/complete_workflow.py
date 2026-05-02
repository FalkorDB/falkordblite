#!/usr/bin/env python3
"""
Complete workflow example for FalkorDBLite.

Demonstrates the full lifecycle:
  1. Create a database
  2. Create a graph
  3. Add nodes and edges
  4. Parameterized queries
  5. Persistence verification
  6. Multi-graph isolation
  7. Cleanup

Requirements: Python 3.12+, falkordblite installed
"""
import os
import sys
import tempfile

# Add the project root to path for development
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from redislite.falkordb_client import FalkorDB


def main():
    # Use a temporary file for the database
    db_path = os.path.join(tempfile.mkdtemp(), "example.db")

    # --- 1. Create a database ---
    print("1. Creating FalkorDB instance...")
    db = FalkorDB(db_path)
    print(f"   Database created at: {db_path}")

    # --- 2. Create a graph ---
    print("\n2. Creating 'social' graph...")
    social = db.select_graph("social")

    # --- 3. Add nodes and edges ---
    print("\n3. Adding nodes and edges...")
    social.query("""
        CREATE (alice:Person {name: 'Alice', age: 30}),
               (bob:Person {name: 'Bob', age: 25}),
               (carol:Person {name: 'Carol', age: 28}),
               (alice)-[:KNOWS {since: 2020}]->(bob),
               (bob)-[:KNOWS {since: 2021}]->(carol),
               (alice)-[:KNOWS {since: 2019}]->(carol)
    """)
    result = social.query("MATCH (n) RETURN count(n) AS node_count")
    print(f"   Nodes created: {result.result_set[0][0]}")

    result = social.query("MATCH ()-[r]->() RETURN count(r) AS edge_count")
    print(f"   Edges created: {result.result_set[0][0]}")

    # --- 4. Parameterized queries ---
    print("\n4. Parameterized queries...")
    result = social.query(
        "MATCH (p:Person {name: $name})-[:KNOWS]->(friend) RETURN friend.name",
        params={"name": "Alice"},
    )
    print(f"   Alice's friends: {[row[0] for row in result.result_set]}")

    # Add a new person with parameters
    social.query(
        "CREATE (p:Person {name: $name, age: $age})",
        params={"name": "Dave", "age": 35},
    )
    result = social.query("MATCH (p:Person) RETURN p.name ORDER BY p.name")
    print(f"   All people: {[row[0] for row in result.result_set]}")

    # --- 5. Persistence verification ---
    print("\n5. Verifying persistence...")
    # Close and reopen the same database file
    del social
    del db

    db = FalkorDB(db_path)
    social = db.select_graph("social")
    result = social.query("MATCH (p:Person) RETURN p.name ORDER BY p.name")
    print(f"   People after reopen: {[row[0] for row in result.result_set]}")

    # --- 6. Multi-graph isolation ---
    print("\n6. Multi-graph isolation...")
    products = db.select_graph("products")
    products.query("CREATE (p:Product {name: 'Laptop', price: 999})")
    products.query("CREATE (p:Product {name: 'Phone', price: 699})")

    # Verify graphs are isolated
    social_count = social.query("MATCH (n) RETURN count(n)").result_set[0][0]
    product_count = products.query("MATCH (n) RETURN count(n)").result_set[0][0]
    print(f"   Nodes in 'social': {social_count}")
    print(f"   Nodes in 'products': {product_count}")

    all_graphs = db.list_graphs()
    print(f"   All graphs: {all_graphs}")

    # --- 7. Cleanup ---
    print("\n7. Cleanup...")
    social.delete()
    products.delete()
    print("   Graphs deleted.")

    # Remove the database file
    del db
    os.unlink(db_path)
    print(f"   Database file removed.")

    print("\nComplete workflow finished successfully!")


if __name__ == "__main__":
    main()

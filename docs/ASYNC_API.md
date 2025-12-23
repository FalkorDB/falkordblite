# Async API Documentation

FalkorDBLite provides full async/await support for both Redis and FalkorDB operations. The async API is designed for use in asynchronous applications, web frameworks (like FastAPI, aiohttp), and scenarios where you need to handle multiple concurrent operations efficiently.

## Installation

The async API is included in the standard FalkorDBLite installation:

```bash
pip install falkordblite
```

## Overview

The async API includes:

- **`AsyncRedis`**: Async version of the Redis client
- **`AsyncStrictRedis`**: Alias for AsyncRedis (for compatibility)
- **`AsyncFalkorDB`**: Async version of the FalkorDB client
- **`AsyncGraph`**: Async graph interface for executing Cypher queries

## Quick Start

### Basic Async Redis Operations

```python
import asyncio
from redislite import AsyncRedis

async def main():
    # Create an async Redis connection
    redis = AsyncRedis('/tmp/redis.db')
    
    try:
        # Set and get values
        await redis.set('key', 'value')
        value = await redis.get('key')
        print(value)  # b'value'
    finally:
        await redis.close()

asyncio.run(main())
```

### Basic Async FalkorDB Operations

```python
import asyncio
from redislite import AsyncFalkorDB

async def main():
    # Create an async FalkorDB instance
    db = AsyncFalkorDB('/tmp/falkordb.db')
    
    try:
        # Select a graph
        g = db.select_graph('social')
        
        # Execute a query
        await g.query('CREATE (n:Person {name: "Alice", age: 30}) RETURN n')
        
        # Read data
        result = await g.query('MATCH (n:Person) RETURN n.name, n.age')
        for row in result.result_set:
            print(row)
        
        # Clean up the graph
        await g.delete()
    finally:
        await db.close()

asyncio.run(main())
```

## Context Managers

Both `AsyncRedis` and `AsyncFalkorDB` support async context managers for automatic cleanup:

```python
import asyncio
from redislite import AsyncFalkorDB

async def main():
    async with AsyncFalkorDB('/tmp/falkordb.db') as db:
        g = db.select_graph('social')
        await g.query('CREATE (n:Person {name: "Alice"}) RETURN n')
        result = await g.query('MATCH (n:Person) RETURN n')
        # Automatically closed when exiting the context

asyncio.run(main())
```

## Concurrent Operations

One of the key benefits of the async API is the ability to run multiple operations concurrently:

```python
import asyncio
from redislite import AsyncRedis

async def main():
    redis = AsyncRedis('/tmp/redis.db')
    
    try:
        # Execute multiple operations concurrently
        await asyncio.gather(
            redis.set('key1', 'value1'),
            redis.set('key2', 'value2'),
            redis.set('key3', 'value3'),
        )
        
        # Fetch multiple keys concurrently
        results = await asyncio.gather(
            redis.get('key1'),
            redis.get('key2'),
            redis.get('key3'),
        )
        print(results)  # [b'value1', b'value2', b'value3']
    finally:
        await redis.close()

asyncio.run(main())
```

## Graph Database Operations

### Creating Nodes and Relationships

```python
import asyncio
from redislite import AsyncFalkorDB

async def main():
    db = AsyncFalkorDB('/tmp/social.db')
    
    try:
        g = db.select_graph('social')
        
        # Create multiple nodes concurrently
        await asyncio.gather(
            g.query('CREATE (p:Person {name: "Alice", age: 30})'),
            g.query('CREATE (p:Person {name: "Bob", age: 25})'),
            g.query('CREATE (p:Person {name: "Carol", age: 28})'),
        )
        
        # Create relationships
        await g.query('''
            MATCH (a:Person {name: "Alice"}), (b:Person {name: "Bob"})
            CREATE (a)-[:KNOWS]->(b)
        ''')
        
        # Query the graph
        result = await g.query('MATCH (p:Person) RETURN p.name, p.age')
        for row in result.result_set:
            print(f"{row[0]}, age {row[1]}")
    finally:
        await db.close()

asyncio.run(main())
```

### Read-Only Queries

For read-only operations, use `ro_query` for better performance:

```python
async def main():
    async with AsyncFalkorDB('/tmp/social.db') as db:
        g = db.select_graph('social')
        
        # Read-only query
        result = await g.ro_query('''
            MATCH (p:Person)-[:KNOWS]->(f:Person)
            RETURN p.name, f.name
        ''')
        
        for row in result.result_set:
            print(f"{row[0]} knows {row[1]}")

asyncio.run(main())
```

### Working with Multiple Graphs

```python
async def main():
    async with AsyncFalkorDB('/tmp/multi.db') as db:
        # Create different graphs for different domains
        users = db.select_graph('users')
        products = db.select_graph('products')
        
        # Execute queries on different graphs concurrently
        await asyncio.gather(
            users.query('CREATE (u:User {name: "Alice"})'),
            products.query('CREATE (p:Product {name: "Laptop"})'),
        )
        
        # List all graphs
        graphs = await db.list_graphs()
        print(f"Graphs: {graphs}")

asyncio.run(main())
```

## Integration with Web Frameworks

### FastAPI Example

```python
from fastapi import FastAPI
from redislite import AsyncFalkorDB

app = FastAPI()

# Initialize the database
db = AsyncFalkorDB('/tmp/api.db')

@app.on_event("startup")
async def startup():
    # Database is already initialized
    pass

@app.on_event("shutdown")
async def shutdown():
    await db.close()

@app.get("/person/{name}")
async def get_person(name: str):
    g = db.select_graph('social')
    result = await g.ro_query(
        f'MATCH (p:Person {{name: "{name}"}}) RETURN p.name, p.age'
    )
    if result.result_set:
        return {"name": result.result_set[0][0], "age": result.result_set[0][1]}
    return {"error": "Person not found"}

@app.post("/person")
async def create_person(name: str, age: int):
    g = db.select_graph('social')
    await g.query(f'CREATE (p:Person {{name: "{name}", age: {age}}})')
    return {"status": "created", "name": name, "age": age}
```

### aiohttp Example

```python
from aiohttp import web
from redislite import AsyncFalkorDB

db = AsyncFalkorDB('/tmp/web.db')

async def handle_get_person(request):
    name = request.match_info['name']
    g = db.select_graph('social')
    result = await g.ro_query(
        f'MATCH (p:Person {{name: "{name}"}}) RETURN p.name, p.age'
    )
    if result.result_set:
        return web.json_response({
            "name": result.result_set[0][0],
            "age": result.result_set[0][1]
        })
    return web.json_response({"error": "Person not found"}, status=404)

async def on_cleanup(app):
    await db.close()

app = web.Application()
app.router.add_get('/person/{name}', handle_get_person)
app.on_cleanup.append(on_cleanup)

web.run_app(app)
```

## Performance Considerations

1. **Concurrent Operations**: Use `asyncio.gather()` to execute multiple independent operations concurrently
2. **Read-Only Queries**: Use `ro_query()` instead of `query()` for read operations when possible
3. **Connection Pooling**: The async client uses connection pooling internally for efficient resource usage
4. **Context Managers**: Always use context managers or explicit `close()` calls to properly clean up resources

## API Reference

### AsyncRedis

```python
class AsyncRedis:
    def __init__(self, dbfilename=None, serverconfig=None, **kwargs):
        """Create an async Redis connection with embedded server."""
    
    async def close(self):
        """Close the connection and cleanup the server."""
    
    async def __aenter__(self):
        """Async context manager entry."""
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
    
    # All standard Redis commands are available as async methods
    async def set(self, name, value):
        """Set a key-value pair."""
    
    async def get(self, name):
        """Get a value by key."""
    
    # ... and all other Redis commands
```

### AsyncFalkorDB

```python
class AsyncFalkorDB:
    def __init__(self, dbfilename=None, serverconfig=None, **kwargs):
        """Create an async FalkorDB instance."""
    
    def select_graph(self, name: str) -> AsyncGraph:
        """Select a graph by name."""
    
    async def list_graphs(self) -> List[str]:
        """List all graphs."""
    
    async def close(self):
        """Close the connection and cleanup."""
    
    async def flushdb(self):
        """Flush the current database."""
    
    async def execute_command(self, *args, **kwargs):
        """Execute a Redis command."""
```

### AsyncGraph

```python
class AsyncGraph:
    def __init__(self, client: AsyncRedis, name: str):
        """Initialize an async graph."""
    
    async def query(self, q: str, params: dict = None, timeout: int = None):
        """Execute a Cypher query."""
    
    async def ro_query(self, q: str, params: dict = None, timeout: int = None):
        """Execute a read-only Cypher query."""
    
    async def delete(self):
        """Delete the graph."""
    
    async def copy(self, clone: str) -> AsyncGraph:
        """Create a copy of the graph."""
```

## Error Handling

```python
import asyncio
from redislite import AsyncFalkorDB

async def main():
    db = AsyncFalkorDB('/tmp/falkordb.db')
    
    try:
        g = db.select_graph('social')
        
        try:
            result = await g.query('INVALID CYPHER QUERY')
        except Exception as e:
            print(f"Query error: {e}")
        
        # Continue with valid operations
        result = await g.query('MATCH (n) RETURN n LIMIT 10')
        
    finally:
        await db.close()

asyncio.run(main())
```

## Differences from Sync API

The async API is functionally equivalent to the synchronous API, with these key differences:

1. All I/O operations are async and must be awaited
2. Use `async with` instead of `with` for context managers
3. Supports concurrent operations via `asyncio.gather()`
4. All methods that perform I/O are coroutines (async def)

## Migration from Sync to Async

Migrating from the sync API to async is straightforward:

**Before (Sync):**
```python
from redislite import FalkorDB

db = FalkorDB('/tmp/db.db')
g = db.select_graph('social')
result = g.query('MATCH (n:Person) RETURN n')
db.close()
```

**After (Async):**
```python
import asyncio
from redislite import AsyncFalkorDB

async def main():
    db = AsyncFalkorDB('/tmp/db.db')
    g = db.select_graph('social')
    result = await g.query('MATCH (n:Person) RETURN n')
    await db.close()

asyncio.run(main())
```

Or with context managers:

```python
import asyncio
from redislite import AsyncFalkorDB

async def main():
    async with AsyncFalkorDB('/tmp/db.db') as db:
        g = db.select_graph('social')
        result = await g.query('MATCH (n:Person) RETURN n')

asyncio.run(main())
```

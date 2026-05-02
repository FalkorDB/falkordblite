# FalkorDBLite

[![CI](https://github.com/FalkorDB/falkordblite/actions/workflows/ci.yml/badge.svg)](https://github.com/FalkorDB/falkordblite/actions/workflows/ci.yml)
[![Publish to PyPI](https://github.com/FalkorDB/falkordblite/actions/workflows/publish.yml/badge.svg)](https://github.com/FalkorDB/falkordblite/actions/workflows/publish.yml)
[![Coverage](https://codecov.io/gh/FalkorDB/falkordblite/branch/master/graph/badge.svg)](https://codecov.io/gh/FalkorDB/falkordblite)
[![License](https://img.shields.io/pypi/l/falkordblite.svg)](https://pypi.python.org/pypi/falkordblite/)

## Description

FalkorDBLite is a self-contained Python interface to the FalkorDB graph database.

It provides enhanced versions of the Redis-Py Python bindings with FalkorDB graph database functionality.  Key features include:

* **Easy to use** - It provides a built-in Redis server with FalkorDB module that is automatically installed, configured and managed when the bindings are used.
* **Graph Database** - Full support for FalkorDB graph operations using Cypher queries through a simple Python API.
* **Flexible** - Create a single server shared by multiple programs or multiple independent servers with graph capabilities.
* **Compatible** - Provides both Redis key-value operations and FalkorDB graph operations in a unified interface.
* **Secure** - Uses a secure default Redis configuration that is only accessible by the creating user on the computer system it is run on.

## Installation

To install falkordblite, simply:

```console
$ pip install falkordblite
```

### Verifying Installation

After installation, you can verify that everything is working correctly:

```console
$ python verify_install.py
```

This will test:
- Package imports
- FalkorDB instance creation
- Basic graph operations

## Requirements

The falkordblite module requires Python 3.12 or higher.

### Runtime Requirements

The package requires the following Python packages (automatically installed with pip):
- `redis>=4.5` - Redis Python client
- `psutil` - Process and system utilities
- `setuptools>38.0` - Build system

### macOS Runtime Requirements

**Important:** The FalkorDB module requires the OpenMP runtime library (`libomp`). 
If you encounter an error like `Library not loaded: /opt/homebrew/opt/libomp/lib/libomp.dylib`, 
install it using Homebrew:

```bash
brew install libomp
```


## Getting Started

FalkorDBLite provides multiple interfaces:

1. **FalkorDB Graph API** - A graph database interface using Cypher queries
2. **Redis API** - Traditional Redis key-value operations (via redislite compatibility)
3. **Async API** - Asynchronous versions of both FalkorDB and Redis interfaces for async/await usage

The package includes both Redis and the FalkorDB module, automatically configured and managed.
    
## Examples

Here are some examples of using the falkordblite module.

### Using FalkorDB Graph Database

Here we create a graph database, add some nodes and relationships, and query them using Cypher:

```python
from redislite.falkordb_client import FalkorDB

# Create a FalkorDB instance with embedded Redis + FalkorDB
db = FalkorDB('/tmp/falkordb.db')

# Select a graph
g = db.select_graph('social')

# Create nodes with Cypher
result = g.query('CREATE (p:Person {name: "Alice", age: 30}) RETURN p')
result = g.query('CREATE (p:Person {name: "Bob", age: 25}) RETURN p')

# Create a relationship
result = g.query('''
    MATCH (a:Person {name: "Alice"}), (b:Person {name: "Bob"})
    CREATE (a)-[r:KNOWS]->(b)
    RETURN r
''')

# Query the graph
result = g.query('MATCH (p:Person) RETURN p.name, p.age')
for row in result.result_set:
    print(row)

# Read-only query
result = g.ro_query('MATCH (p:Person)-[r:KNOWS]->(f) RETURN p.name, f.name')

# Delete the graph when done
g.delete()
```

### Using Redis Key-Value Operations

You can still use traditional Redis operations alongside graph operations:

```python
from redislite import Redis

redis_connection = Redis('/tmp/redis.db')
redis_connection.keys()
# []
redis_connection.set('key', 'value')
# True
redis_connection.get('key')
# b'value'
```

### Persistence

FalkorDB data persists between sessions. Open the same database file to access previously stored graphs:

```python
from redislite.falkordb_client import FalkorDB

# Open the same database
db = FalkorDB('/tmp/falkordb.db')
g = db.select_graph('social')

# Data from previous session is still there
result = g.query('MATCH (p:Person) RETURN p.name')
for row in result.result_set:
    print(row)
```

## Compatibility

It's possible to MonkeyPatch the normal Redis classes to allow modules 
that use Redis to use the redislite classes.  Here we patch Redis and use the 
redis_collections module.

```python
import redislite.patch
redislite.patch.patch_redis()
import redis_collections

td = redis_collections.Dict()
td['foo'] = 'bar'
td.keys()
# ['foo']
```

## Running and using Multiple servers

Redislite will start a new server if the redis rdb filename isn't specified or is new.  In this example we start 10 separate redis servers and set the value of the key 'servernumber' to a different value in each server.  

Then we access the value of 'servernumber' and print it.

```python
import redislite

servers = {}
for redis_server_number in range(10):
    servers[redis_server_number] = redislite.Redis()
    servers[redis_server_number].set('servernumber', redis_server_number)

for redis_server in servers.values():
    print(redis_server.get('servernumber'))
# b'0'
# b'1'
# b'2'
# b'3'
# b'4'
# b'5'
# b'6'
# b'7'
# b'8'
# b'9'
```

## Multiple Servers with different configurations in the same script

It's possible to spin up multiple instances with different
configuration settings for the Redis server.  Here is an example that sets up 2
redis server instances.  One instance is configured to listen on port 8002, the
second instance is a read-only slave of the first instance.


```python
import redislite

master = redislite.Redis(serverconfig={'port': '8002'})
slave = redislite.Redis(serverconfig={'slaveof': "127.0.0.1 8002"})
slave.keys()
# []
master.set('key', 'value')
# True
master.keys()
# ['key']
slave.keys()
# ['key']
```

## FalkorDB-Specific Features

### Graph Database with Cypher Queries

FalkorDBLite provides full support for graph database operations using Cypher queries:

```python
from redislite.falkordb_client import FalkorDB

db = FalkorDB('/tmp/graphs.db')
g = db.select_graph('social')

# Create a graph with nodes and relationships
g.query('''
    CREATE (alice:Person {name: "Alice", age: 30}),
           (bob:Person {name: "Bob", age: 25}),
           (carol:Person {name: "Carol", age: 28}),
           (alice)-[:KNOWS]->(bob),
           (bob)-[:KNOWS]->(carol),
           (alice)-[:KNOWS]->(carol)
''')

# Find all friends of Alice
result = g.query('''
    MATCH (p:Person {name: "Alice"})-[:KNOWS]->(friend)
    RETURN friend.name, friend.age
''')
for row in result.result_set:
    print(f"Friend: {row[0]}, Age: {row[1]}")
```

### Multiple Graphs

Work with multiple independent graphs in the same database:

```python
from redislite.falkordb_client import FalkorDB

db = FalkorDB('/tmp/multi.db')

# Create different graphs for different domains
users = db.select_graph('users')
products = db.select_graph('products')
transactions = db.select_graph('transactions')

# Each graph is independent
users.query('CREATE (u:User {name: "Alice"})')
products.query('CREATE (p:Product {name: "Laptop"})')

# List all graphs
all_graphs = db.list_graphs()
print(all_graphs)
```

## Async API

FalkorDBLite provides async/await support for non-blocking operations. This is particularly useful for web applications, concurrent workloads, and high-performance scenarios.

### Async FalkorDB Graph Operations

Use `AsyncFalkorDB` and `AsyncGraph` for asynchronous graph database operations:

```python
import asyncio
from redislite.async_falkordb_client import AsyncFalkorDB

async def main():
    # Create an async FalkorDB instance
    db = AsyncFalkorDB('/tmp/falkordb_async.db')
    
    # Select a graph
    g = db.select_graph('social')
    
    # Create nodes asynchronously using parameterized queries
    await g.query(
        'CREATE (p:Person {name: $name, age: $age}) RETURN p',
        params={'name': 'Alice', 'age': 30}
    )
    await g.query(
        'CREATE (p:Person {name: $name, age: $age}) RETURN p',
        params={'name': 'Bob', 'age': 25}
    )
    
    # Create a relationship using parameterized queries
    await g.query(
        '''
        MATCH (a:Person {name: $name_a}), (b:Person {name: $name_b})
        CREATE (a)-[r:KNOWS]->(b)
        RETURN r
        ''',
        params={'name_a': 'Alice', 'name_b': 'Bob'}
    )
    
    # Query the graph asynchronously
    result = await g.query('MATCH (p:Person) RETURN p.name, p.age')
    for row in result.result_set:
        print(row)
    
    # Read-only query
    result = await g.ro_query('MATCH (p:Person)-[r:KNOWS]->(f) RETURN p.name, f.name')
    
    # Clean up
    await g.delete()
    await db.close()

# Run the async function
asyncio.run(main())
```

### Async Redis Operations

Use `AsyncRedis` for asynchronous Redis key-value operations:

```python
import asyncio
from redislite.async_client import AsyncRedis

async def main():
    # Create an async Redis connection
    redis_conn = AsyncRedis('/tmp/redis_async.db')
    
    # Async set and get
    await redis_conn.set('key', 'value')
    value = await redis_conn.get('key')
    print(value)  # b'value'
    
    # Multiple operations concurrently
    await asyncio.gather(
        redis_conn.set('key1', 'value1'),
        redis_conn.set('key2', 'value2'),
        redis_conn.set('key3', 'value3'),
    )
    
    # Get all keys
    keys = await redis_conn.keys()
    print(keys)
    
    await redis_conn.close()

asyncio.run(main())
```

### Async Context Manager

Both `AsyncFalkorDB` and `AsyncRedis` support async context managers for automatic cleanup:

```python
import asyncio
from redislite.async_falkordb_client import AsyncFalkorDB

async def main():
    async with AsyncFalkorDB('/tmp/falkordb.db') as db:
        g = db.select_graph('social')
        result = await g.query(
            'CREATE (n:Person {name: $name}) RETURN n',
            params={'name': 'Alice'}
        )
        print(result.result_set)
    # Connection is automatically closed

asyncio.run(main())
```

### Concurrent Graph Operations

The async API enables efficient concurrent operations:

```python
import asyncio
from redislite.async_falkordb_client import AsyncFalkorDB

async def create_person(graph, name, age):
    """Create a person node asynchronously"""
    query = 'CREATE (p:Person {name: $name, age: $age}) RETURN p'
    return await graph.query(query, params={'name': name, 'age': age})

async def main():
    db = AsyncFalkorDB('/tmp/social.db')
    g = db.select_graph('social')
    
    # Create multiple nodes concurrently
    people = [
        ('Alice', 30),
        ('Bob', 25),
        ('Carol', 28),
        ('Dave', 35),
    ]
    
    # Execute all creates concurrently
    await asyncio.gather(
        *[create_person(g, name, age) for name, age in people]
    )
    
    # Query all people
    result = await g.query('MATCH (p:Person) RETURN p.name, p.age ORDER BY p.name')
    for row in result.result_set:
        print(f"{row[0]}, age {row[1]}")
    
    await g.delete()
    await db.close()

asyncio.run(main())
```

For complete async API documentation including web framework integration, see [docs/ASYNC_API.md](docs/ASYNC_API.md).

## More Information

FalkorDBLite combines the power of Redis and FalkorDB graph database in an embedded Python package.

- FalkorDB: https://www.falkordb.com/
- FalkorDB Documentation: https://docs.falkordb.com/
- FalkorDB Python Client: https://github.com/FalkorDB/falkordb-py

FalkorDBLite is Free software under the New BSD license, see LICENSE.txt for details.

## Building from Source

If you want to build FalkorDBLite from source instead of using the PyPI package, follow these instructions.

### System Requirements for Building

#### Linux

Make sure Python development headers and build tools are available when building from source.

On Ubuntu/Debian systems, install them with:

```bash
apt-get install python3-dev build-essential
```

On Redhat/Fedora systems, install them with:

```bash
yum install python3-devel gcc make
```

#### macOS

To build FalkorDBLite on macOS from the sdist package, you will need
the XCode command line utilities installed. If you do not have xcode
installed on recent macOS releases, they can be installed by running:

```bash
xcode-select --install
```

#### Windows

Redislite can be installed on newer releases of Windows 10 under the Bash on Ubuntu shell.

Install it using the instructions at https://msdn.microsoft.com/commandline/wsl/install_guide 

Then start the bash shell and install the python-dev package as follows:

`apt-get install python-dev`

### Building and Installing

To build from source:

```console
$ pip install -r requirements.txt
$ python setup.py install
```

### Development Installation

For development or working from source in a virtual environment:

```console
# Create and activate a virtual environment
$ python3 -m venv venv
$ source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install build dependencies
$ pip install setuptools wheel

# Install runtime dependencies
$ pip install -r requirements.txt

# Build the project (this compiles Redis and copies binaries automatically)
$ python setup.py build

# Install in editable mode for development
$ pip install -e .
```

The `python setup.py build` command will:
- Compile Redis from source
- Download the FalkorDB module
- Automatically copy binaries to `redislite/bin/` with proper permissions

**Note:** If you encounter issues, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for details.

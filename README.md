# FalkorDBLite

[![CI/CD](https://img.shields.io/badge/CI/CD-Screwdriver-blue.svg)](https://screwdriver.cd/)
[![Build Status](https://cd.screwdriver.cd/pipelines/2880/badge)](https://cd.screwdriver.cd/pipelines/2880)
[![Codestyle](https://img.shields.io/badge/code%20style-pep8-blue.svg)](https://www.python.org/dev/peps/pep-0008/)
[![Coverage](https://codecov.io/gh/yahoo/redislite/branch/master/graph/badge.svg)](https://codecov.io/gh/yahoo/redislite)
[![License](https://img.shields.io/pypi/l/redislite.svg)](https://pypi.python.org/pypi/redislite/)

## Description

FalkorDBLite is a self-contained Python interface to the FalkorDB graph database.

It provides enhanced versions of the Redis-Py Python bindings with FalkorDB graph database functionality.  Key features include:

* **Easy to use** - It provides a built-in Redis server with FalkorDB module that is automatically installed, configured and managed when the bindings are used.
* **Graph Database** - Full support for FalkorDB graph operations using Cypher queries through a simple Python API.
* **Flexible** - Create a single server shared by multiple programs or multiple independent servers with graph capabilities.
* **Compatible** - Provides both Redis key-value operations and FalkorDB graph operations in a unified interface.
* **Secure** - Uses a secure default Redis configuration that is only accessible by the creating user on the computer system it is run on.

## Requirements

The falkordblite module requires Python 3.8 or higher.

### Python Dependencies

The package requires the following Python packages:
- `redis>=4.5` - Redis Python client
- `psutil` - Process and system utilities
- `setuptools>38.0` - Build system

These are automatically installed when using `pip install` or by installing from `requirements.txt`.

### System Requirements on Linux

Make sure Python development headers and build tools are available when building from source.

On Ubuntu/Debian systems, install them with:

```bash
apt-get install python3-dev build-essential
```

On Redhat/Fedora systems, install them with:

```bash
yum install python3-devel gcc make
```

### Installing requirements on Mac OSX

Redislite for OSX comes as a wheel package by default that can be installed
using current versions of pip.

To install Redislite on MacOSX using the sdist package instead you will need
the XCode command line utilities installed.  If you do not have xcode
installed on recent OSX releases they can be installed by
running:

`xcode-select --install`

### Installing requirements on Microsoft Windows

Redislite can be installed on newer releases of Windows 10 under the Bash on Ubuntu shell.

Install it using the instructions at https://msdn.microsoft.com/commandline/wsl/install_guide 

Then start the bash shell and install the python-dev package as follows:

`apt-get install python-dev`    
    
## Installation

To install falkordblite, simply:

```console
$ pip install falkordblite
```

or from source:

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

# Build and install
$ python setup.py install
```


## Getting Started

FalkorDBLite provides two main interfaces:

1. **FalkorDB Graph API** - A graph database interface using Cypher queries
2. **Redis API** - Traditional Redis key-value operations (via redislite compatibility)

The package includes both Redis and the FalkorDB module, automatically configured and managed.
    
## Examples

Here are some examples of using the falkordblite module.

### Using FalkorDB Graph Database

Here we create a graph database, add some nodes and relationships, and query them using Cypher:

```python
>>> from redislite.falkordb_client import FalkorDB
>>> 
>>> # Create a FalkorDB instance with embedded Redis + FalkorDB
>>> db = FalkorDB('/tmp/falkordb.db')
>>> 
>>> # Select a graph
>>> g = db.select_graph('social')
>>> 
>>> # Create nodes with Cypher
>>> result = g.query('CREATE (p:Person {name: "Alice", age: 30}) RETURN p')
>>> result = g.query('CREATE (p:Person {name: "Bob", age: 25}) RETURN p')
>>> 
>>> # Create a relationship
>>> result = g.query('''
...     MATCH (a:Person {name: "Alice"}), (b:Person {name: "Bob"})
...     CREATE (a)-[r:KNOWS]->(b)
...     RETURN r
... ''')
>>> 
>>> # Query the graph
>>> result = g.query('MATCH (p:Person) RETURN p.name, p.age')
>>> for row in result.result_set:
...     print(row)
>>> 
>>> # Read-only query
>>> result = g.ro_query('MATCH (p:Person)-[r:KNOWS]->(f) RETURN p.name, f.name')
>>> 
>>> # Delete the graph when done
>>> g.delete()
```

### Using Redis Key-Value Operations

You can still use traditional Redis operations alongside graph operations:

```python
>>> from redislite import Redis
>>> redis_connection = Redis('/tmp/redis.db')
>>> redis_connection.keys()
[]
>>> redis_connection.set('key', 'value')
True
>>> redis_connection.get('key')
b'value'
```

### Persistence

FalkorDB data persists between sessions. Open the same database file to access previously stored graphs:

```python
>>> from redislite.falkordb_client import FalkorDB
>>> 
>>> # Open the same database
>>> db = FalkorDB('/tmp/falkordb.db')
>>> g = db.select_graph('social')
>>> 
>>> # Data from previous session is still there
>>> result = g.query('MATCH (p:Person) RETURN p.name')
>>> for row in result.result_set:
...     print(row)
```

## Compatibility

It's possible to MonkeyPatch the normal Redis classes to allow modules 
that use Redis to use the redislite classes.  Here we patch Redis and use the 
redis_collections module.

```python
>>> import redislite.patch
>>> redislite.patch.patch_redis()
>>> import redis_collections
>>> td = redis_collections.Dict()
>>> td['foo']='bar'
>>> td.keys()
['foo']
```

## Running and using Multiple servers

Redislite will start a new server if the redis rdb fileame isn't specified or is new.  In this example we start 10 seperate redis servers and set the value of the key 'servernumber' to a different value in each server.  

Then we access the value of 'servernumber' and print it.

```python
>>> import redislite
>>> servers = {}
>>> for redis_server_number in range(10):
...     servers[redis_server_number] = redislite.Redis()
...     servers[redis_server_number].set('servernumber', redis_server_number)
...
True
True
True
True
True
True
True
True
True
True
>>> for redis_server in servers.values():
...     redis_server.get('servernumber')
...
b'0'
b'1'
b'2'
b'3'
b'4'
b'5'
b'6'
b'7'
b'8'
b'9'
```

## Multiple Servers with different configurations in the same script

It's possible to spin up multiple instances with different
configuration settings for the Redis server.  Here is an example that sets up 2
redis server instances.  One instance is configured to listen on port 8002, the
second instance is a read-only slave of the first instance.


```python
>>> import redislite
>>> master=redislite.Redis(serverconfig={'port': '8002'})
>>> slave=redislite.Redis(serverconfig={'slaveof': "127.0.0.1 8002"})
>>> slave.keys()
[]
>>> master.set('key', 'value')
True
>>> master.keys()
['key']
>>> slave.keys()
['key']
>>>
```

## FalkorDB-Specific Features

### Graph Database with Cypher Queries

FalkorDBLite provides full support for graph database operations using Cypher queries:

```python
>>> from redislite.falkordb_client import FalkorDB
>>> 
>>> db = FalkorDB('/tmp/graphs.db')
>>> g = db.select_graph('social')
>>> 
>>> # Create a graph with nodes and relationships
>>> g.query('''
...     CREATE (alice:Person {name: "Alice", age: 30}),
...            (bob:Person {name: "Bob", age: 25}),
...            (carol:Person {name: "Carol", age: 28}),
...            (alice)-[:KNOWS]->(bob),
...            (bob)-[:KNOWS]->(carol),
...            (alice)-[:KNOWS]->(carol)
... ''')
>>> 
>>> # Find all friends of Alice
>>> result = g.query('''
...     MATCH (p:Person {name: "Alice"})-[:KNOWS]->(friend)
...     RETURN friend.name, friend.age
... ''')
>>> for row in result.result_set:
...     print(f"Friend: {row[0]}, Age: {row[1]}")
```

### Multiple Graphs

Work with multiple independent graphs in the same database:

```python
>>> from redislite.falkordb_client import FalkorDB
>>> 
>>> db = FalkorDB('/tmp/multi.db')
>>> 
>>> # Create different graphs for different domains
>>> users = db.select_graph('users')
>>> products = db.select_graph('products')
>>> transactions = db.select_graph('transactions')
>>> 
>>> # Each graph is independent
>>> users.query('CREATE (u:User {name: "Alice"})')
>>> products.query('CREATE (p:Product {name: "Laptop"})')
>>> 
>>> # List all graphs
>>> all_graphs = db.list_graphs()
>>> print(all_graphs)
```

## More Information

FalkorDBLite combines the power of Redis and FalkorDB graph database in an embedded Python package.

- FalkorDB: https://www.falkordb.com/
- FalkorDB Documentation: https://docs.falkordb.com/
- FalkorDB Python Client: https://github.com/FalkorDB/falkordb-py

FalkorDBLite is Free software under the New BSD license, see LICENSE.txt for details.

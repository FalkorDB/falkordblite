# GitHub Copilot Instructions for FalkorDBLite

## Repository Overview

FalkorDBLite is a self-contained Python interface to the FalkorDB graph database. It provides enhanced versions of Redis-Py Python bindings with FalkorDB graph database functionality, embedding both a Redis server and the FalkorDB module for graph operations.

**Key Features:**
- Embedded Redis server with FalkorDB module (automatically installed and managed)
- Full FalkorDB graph database operations using Cypher queries
- Compatible Redis key-value operations
- **Async API support** for non-blocking operations (AsyncFalkorDB, AsyncRedis)
- Secure default configuration (accessible only by creating user)
- Cross-platform support (Linux x86_64/ARM64, macOS ARM64/x86_64)

## Project Structure

```
falkordblite/
├── .github/              # GitHub Actions workflows and configuration
│   ├── workflows/        # CI/CD pipeline definitions
│   │   ├── ci.yml       # Test, lint, and build workflow
│   │   ├── publish.yml  # PyPI publishing workflow
│   │   └── spellcheck.yml # Spell checking workflow
│   └── INSTRUCTIONS.md  # This file
├── redislite/           # Main package source code
│   ├── __init__.py      # Package initialization and metadata
│   ├── client.py        # Redis client wrapper (sync)
│   ├── async_client.py  # Async Redis client wrapper
│   ├── falkordb_client.py # FalkorDB graph database client (sync)
│   ├── async_falkordb_client.py # Async FalkorDB client
│   ├── configuration.py # Redis server configuration
│   ├── debug.py         # Debug utilities
│   └── patch.py         # Monkey patching utilities
├── tests/               # Test suite
│   ├── test_client.py   # Redis client tests
│   ├── test_falkordb.py # FalkorDB functionality tests (sync)
│   ├── test_async_falkordb.py # Async FalkorDB tests
│   ├── test_configuration.py # Configuration tests
│   └── ...
├── examples/            # Example scripts
│   └── async_example.py # Async API usage examples
├── docs/                # Documentation
├── build_scripts/       # Build helper scripts
├── src/                 # C extension sources (minimal)
├── setup.py            # Package setup and build configuration
├── pyproject.toml      # Build system configuration
├── pytest.ini          # Pytest configuration
├── .pylintrc           # Pylint configuration
└── requirements.txt    # Runtime dependencies
```

## Development Setup

### Prerequisites
- Python 3.12, 3.13, or 3.14 (tested and supported versions in CI)
- Build tools (gcc, make, python3-dev on Linux; Xcode CLI tools on macOS)
- macOS: OpenMP runtime library (`brew install libomp`)

### Installation for Development

```bash
# Clone the repository
git clone https://github.com/FalkorDB/falkordblite.git
cd falkordblite

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install build dependencies
pip install setuptools wheel

# Install runtime dependencies
pip install -r requirements.txt

# Build the project (compiles Redis, downloads FalkorDB module)
python setup.py build

# Install in editable mode for development
pip install -e .
```

The `python setup.py build` command will:
1. Download and compile Redis from source (version 8.2.2)
2. Download the FalkorDB module (version v4.14.7)
3. Copy binaries to `redislite/bin/` with proper permissions

## Key Components

### 1. Redis Client (`redislite/client.py`)
- Wraps redis-py client
- Manages embedded Redis server lifecycle
- Provides standard Redis key-value operations
- Handles server configuration and cleanup

### 2. FalkorDB Client (`redislite/falkordb_client.py`)
- Extends Redis client with graph database capabilities
- Dynamically loads falkordb-py Python package
- Provides `FalkorDB` class for graph operations
- Implements `Graph` class for Cypher query execution

### 3. Configuration (`redislite/configuration.py`)
- Generates Redis server configuration
- Manages server settings and security
- Handles persistence and storage options

### 4. Async Clients (`redislite/async_client.py`, `redislite/async_falkordb_client.py`)
- Async/await support for non-blocking operations
- `AsyncRedis` - Async version of Redis client using redis.asyncio
- `AsyncFalkorDB` - Async version of FalkorDB client
- `AsyncGraph` - Async graph operations with Cypher queries
- Useful for web applications, concurrent workloads, and high-performance scenarios

## Testing

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=redislite --cov-report=xml --cov-report=term-missing

# Run specific test file
pytest tests/test_falkordb.py

# Run async tests specifically
pytest tests/test_async_falkordb.py

# Run specific test
pytest tests/test_falkordb.py::test_graph_operations
```

### Test Strategy
- Unit tests for individual components
- Integration tests for Redis and FalkorDB operations (sync and async)
- Configuration and patching tests
- All tests use pytest framework
- Async tests use asyncio.run() for execution
- Coverage tracking with pytest-cov

### Verification Script
After installation, verify functionality:
```bash
python verify_install.py
```

## Linting and Code Quality

### Pylint
```bash
# Install pylint
pip install pylint

# Run pylint on package
pylint redislite

# With parseable output (CI format)
pylint --output-format=parseable redislite
```

Configuration: `.pylintrc`

### Pycodestyle (PEP 8)
```bash
# Install pycodestyle
pip install pycodestyle

# Run pycodestyle
pycodestyle redislite
```

### Spell Checking
```bash
# Uses pyspelling with .spellcheck.yml configuration
# Wordlist: .wordlist.txt
```

## Build Process

### Building Distribution Packages

```bash
# Build source distribution
python setup.py sdist

# Build wheel
python setup.py bdist_wheel

# Using build module (alternative)
pip install build
python -m build
```

### Environment Variables
- `REDIS_VERSION`: Redis version to use (default: 8.2.2)
- `FALKORDB_VERSION`: FalkorDB module version (default: v4.14.7)

### Platform-Specific Builds
The build process automatically detects platform and downloads appropriate FalkorDB module:
- **Linux x86_64**: falkordb-x64.so
- **Linux ARM64**: falkordb-arm64v8.so
- **macOS ARM64**: falkordb-macos-arm64v8.so
- **macOS x86_64**: Uses ARM64 binary via Rosetta 2 (performance impact)

## CI/CD Workflows

### CI Workflow (`.github/workflows/ci.yml`)
Runs on push and PR to master/main branches:
- **Test**: Python 3.12, 3.13, 3.14 on Ubuntu and macOS with full test suite
- **Verification**: Runs verify_install.py to ensure installation works
- **Lint**: Code quality checks with pylint and pycodestyle
- **Build**: Source distribution and wheel packages
- **Coverage**: Upload to Codecov

### Publish Workflow (`.github/workflows/publish.yml`)
Triggered on release publication:
- Builds packages
- Validates with twine
- Publishes to PyPI using Trusted Publishing (OIDC)

## Coding Standards

### Python Style
- Follow PEP 8 style guide
- Use pylint for code quality checks
- Type hints encouraged but not required
- Docstrings for public APIs (Google or NumPy style)

### File Headers
All source files should include copyright header:
```python
# Copyright (c) 2024, FalkorDB
# Copyrights licensed under the New BSD License
# See the accompanying LICENSE.txt file for terms.
```

### Import Organization
1. Standard library imports
2. Third-party imports
3. Local package imports
4. Use absolute imports for package modules

### Error Handling
- Use specific exception types
- Provide informative error messages
- Clean up resources (files, processes) on errors

## Common Tasks

### Adding New FalkorDB Features
1. Check falkordb-py for upstream API changes
2. Add wrapper methods in `falkordb_client.py` (sync) and/or `async_falkordb_client.py` (async)
3. Maintain compatibility with embedded Redis client
4. Add tests in `tests/test_falkordb.py` (sync) and/or `tests/test_async_falkordb.py` (async)

### Working with Async API
1. Use `AsyncFalkorDB` and `AsyncRedis` for async operations
2. All async operations require `await` keyword
3. Use `asyncio.run()` for top-level execution
4. See `examples/async_example.py` for usage patterns
5. Async clients manage embedded server lifecycle same as sync clients

### Updating Redis Version
1. Set `REDIS_VERSION` environment variable
2. Run `python setup.py build`
3. Test with full test suite
4. Update version in CI workflows

### Updating FalkorDB Module
1. Set `FALKORDB_VERSION` environment variable
2. Run `python setup.py build`
3. Verify module loads correctly
4. Test graph operations

### Debugging
```python
# Use debug module for environment info
python -m redislite.debug
```

## Dependencies

### Runtime Dependencies (requirements.txt)
- `redis>=4.5`: Redis Python client (includes redis.asyncio for async support)
- `psutil`: Process and system utilities
- `setuptools>38.0`: Build system
- `falkordb>=1.2.0`: FalkorDB Python client with async support (dynamically loaded)

### Development Dependencies
- `pytest`: Testing framework
- `pytest-cov`: Coverage reporting
- `pylint`: Code quality checker
- `pycodestyle`: PEP 8 checker

## Troubleshooting

See [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) for common issues:
- Missing OpenMP library on macOS
- Build failures
- Module loading issues
- Binary permissions

## Dependency Management

### Dependabot Configuration
The repository uses Dependabot for automated dependency updates (`.github/dependabot.yml`):
- **Python dependencies**: Daily checks for pip packages
- **GitHub Actions**: Weekly checks for workflow dependencies

Dependabot will automatically create PRs for dependency updates when new versions are available.

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for:
- Bug reporting guidelines
- Feature request process
- Pull request workflow
- Code review expectations

## Resources

- **FalkorDB**: https://www.falkordb.com/
- **FalkorDB Documentation**: https://docs.falkordb.com/
- **FalkorDB Python Client**: https://github.com/FalkorDB/falkordb-py
- **Redis Documentation**: https://redis.io/documentation
- **PyPI Package**: https://pypi.org/project/falkordblite/

## License

FalkorDBLite is Free software under the New BSD license. See [LICENSE.txt](../LICENSE.txt) for details.

# FalkorDBLite Installation Troubleshooting

## Issue Summary

When installing FalkorDBLite with `pip install -e .` (editable/development install), the redis-server and falkordb.so binaries are not automatically copied to the `redislite/bin/` directory, causing the installation verification to fail with:

```
RedisLiteServerStartError: The redis-server process failed to start
```

The root cause is that the FalkorDB module (`falkordb.so`) lacks execute permissions.

## Solution

**As of the latest version, this is handled automatically!** When you run `python setup.py build`, the binaries are automatically copied to `redislite/bin/` with proper permissions.

The correct installation workflow is:

```bash
# Build first (compiles Redis and copies binaries)
python setup.py build

# Then install in editable mode
pip install -e .
```

If for some reason the automatic copy fails, you can manually set up the binaries:

```bash
# Create the bin directory
mkdir -p redislite/bin

# Copy the binaries from the build directory
cp build/scripts-3.13/redis-server redislite/bin/
cp falkordb.so redislite/bin/

# Set executable permissions (critical!)
chmod +x redislite/bin/redis-server
chmod +x redislite/bin/falkordb.so
```

## Verification

After setup, verify the installation:

```bash
# Activate your virtual environment first
source venv/bin/activate

# Run the verification script
python3 verify_install.py
```

You should see:
```
==================================================
✓ All tests passed (2/2)
==================================================
```

## Alternative: Production Install

For a production-ready installation that automatically handles all setup:

```bash
# Build and install (not editable)
python setup.py install

# Or use pip without -e flag
pip install .
```

This triggers the full build process that:
1. Compiles Redis from source
2. Copies binaries to the correct location
3. Sets proper permissions
4. Updates package metadata

## Why Editable Install Doesn't Work Out-of-the-Box

The `pip install -e .` command creates a development install that links to your source directory without running the full `setup.py` build and install commands. This means:

- The `BuildRedis` class doesn't copy files to `build/scripts-*`
- The `InstallRedis` class doesn't copy files to `redislite/bin/`
- File permissions aren't automatically set

## For Developers

If you're working on FalkorDBLite development:

1. Always build first: `python setup.py build`
2. Then install in editable mode: `pip install -e .`
3. Manually copy binaries as shown above
4. Or use the production install for testing: `pip install .`

## Common Errors and Solutions

### Error: "No module named 'redis'"
**Solution**: Install dependencies first:
```bash
pip install -r requirements.txt
```

### Error: "It does not have execute permissions"
**Solution**: The falkordb.so module needs execute permissions:
```bash
chmod +x redislite/bin/falkordb.so
```

### Error: "redis-server process failed to start"
**Check:**
1. Does `redislite/bin/redis-server` exist?
2. Does `redislite/bin/falkordb.so` exist?
3. Do both have execute permissions?
4. Test manually: `./redislite/bin/redis-server --version`

## System Requirements

Make sure you have the required build tools:

**Ubuntu/Debian:**
```bash
apt-get install python3-dev build-essential
```

**RHEL/Fedora:**
```bash
yum install python3-devel gcc make
```

## Testing Your Installation

Quick test in Python:

```python
from redislite.falkordb_client import FalkorDB

# Create a database
db = FalkorDB('/tmp/test.db')

# Create a graph
g = db.select_graph('test')

# Run a query
result = g.query('CREATE (n:Test {value: 1}) RETURN n')
print(f"Success! Created node: {result.result_set}")

# Cleanup
g.delete()
```

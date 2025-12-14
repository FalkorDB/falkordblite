# Version Management

This document describes how to update Redis and FalkorDB versions in the FalkorDBLite project.

## Centralized Configuration

Version information is now centralized to make updates easier and prevent mistakes. The primary source of truth is defined in the following locations:

### Primary Configuration Files

1. **`.versions.yml`** - Central reference file documenting current versions
2. **`.github/workflows/ci.yml`** - Global `env` section at the workflow level
3. **`.github/workflows/publish.yml`** - Global `env` section at the workflow level
4. **`screwdriver.yaml`** - Shared environment variables section

### Version Defaults in Code

The following Python files have default version values that can be overridden by environment variables:
- `setup.py` - REDIS_VERSION and FALKORDB_VERSION defaults
- `build_scripts/update_redis_server.py` - redis_version default

## How to Update Versions

To update Redis or FalkorDB versions across the entire project:

### 1. Update `.versions.yml`
Edit the file and update the appropriate version numbers:
```yaml
redis_version: '8.2.2'          # Current Redis version
falkordb_version: 'v4.14.7'     # Current FalkorDB version
redis_version_legacy: '6.2.14'  # Legacy Redis version for specific builds
```

### 2. Update GitHub Actions Workflows
Edit the global `env` section in both workflow files:

**`.github/workflows/ci.yml`**:
```yaml
env:
  REDIS_VERSION: '8.2.2'
  FALKORDB_VERSION: 'v4.14.7'
  REDIS_VERSION_LEGACY: '6.2.14'
```

**`.github/workflows/publish.yml`**:
```yaml
env:
  REDIS_VERSION: '8.2.2'
  FALKORDB_VERSION: 'v4.14.7'
```

### 3. Update Screwdriver Configuration
Edit the shared environment section in `screwdriver.yaml`:
```yaml
shared:
  environment:
    REDIS_VERSION: '6.2.14'
    FALKORDB_VERSION: 'v4.14.7'
```

### 4. Update Python Defaults (if needed)
The default values in `setup.py` and `build_scripts/update_redis_server.py` serve as fallbacks when environment variables are not set. Update them to match the primary versions:

**`setup.py`**:
```python
REDIS_VERSION = os.environ.get('REDIS_VERSION', '8.2.2')
FALKORDB_VERSION = os.environ.get('FALKORDB_VERSION', 'v4.14.7')
```

**`build_scripts/update_redis_server.py`**:
```python
redis_version = os.environ.get('REDIS_VERSION', '8.2.2')
```

## Version Differences

Note that some components may use different Redis versions:
- **Main CI/CD pipeline**: Uses the current Redis version (8.2.2)
- **Legacy builds** (e.g., build-wheels job in ci.yml): Uses the legacy version (6.2.14)

This is intentional to support different build environments and compatibility requirements.

## Testing After Updates

After updating versions:

1. Run local builds to verify the new versions work:
   ```bash
   REDIS_VERSION=X.Y.Z FALKORDB_VERSION=vA.B.C python setup.py build
   ```

2. Check CI/CD workflows to ensure they pass with the new versions

3. Verify the downloaded binaries are the correct versions

## Environment Variable Override

All version settings can be overridden by setting environment variables:
```bash
export REDIS_VERSION=8.2.2
export FALKORDB_VERSION=v4.14.7
```

This is particularly useful for:
- Testing different versions locally
- CI/CD pipeline customization
- Build automation scripts

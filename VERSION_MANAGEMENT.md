# Version Management

This document describes how to update Redis and FalkorDB versions in the FalkorDBLite project.

## Centralized Configuration

Version information is now centralized in a **single source of truth** to make updates easier and prevent mistakes.

### Configuration Files

1. **`.versions.yml`** - **PRIMARY SOURCE OF TRUTH** - All version numbers are defined here
2. **`.github/workflows/ci.yml`** - Reads versions from `.versions.yml` at runtime
3. **`.github/workflows/publish.yml`** - Reads versions from `.versions.yml` at runtime
4. **`screwdriver.yaml`** - Configuration for Screwdriver CI - Should be manually synced with `.versions.yml`
5. **`setup.py`** - Has fallback defaults that should match `.versions.yml`
6. **`build_scripts/update_redis_server.py`** - Has fallback defaults that should match `.versions.yml`

**Note**: GitHub Actions workflows automatically read from `.versions.yml` using Python's YAML parser. Python scripts use environment variables with fallback defaults.

### Version Defaults in Code

The following Python files have default version values that can be overridden by environment variables:
- `setup.py` - REDIS_VERSION and FALKORDB_VERSION defaults
- `build_scripts/update_redis_server.py` - redis_version default

## How to Update Versions

To update Redis or FalkorDB versions across the entire project, you only need to update **one file**:

### 1. Update `.versions.yml`
This is the **only** change needed for GitHub Actions workflows:

```yaml
redis_version: '8.2.2'          # Current Redis version
falkordb_version: 'v4.14.7'     # Current FalkorDB version
```

The GitHub Actions workflows (`.github/workflows/ci.yml` and `.github/workflows/publish.yml`) will automatically read these values.

### 2. Update Screwdriver Configuration (if used)
If you use Screwdriver CI, manually sync the values in `screwdriver.yaml`:

```yaml
shared:
  environment:
    REDIS_VERSION: '8.2.2'
    FALKORDB_VERSION: 'v4.14.7'
```

### 3. Update Python Defaults (optional)
The default values in `setup.py` and `build_scripts/update_redis_server.py` serve as fallbacks when environment variables are not set. It's good practice to keep them in sync:

**`setup.py`**:
```python
REDIS_VERSION = os.environ.get('REDIS_VERSION', '8.2.2')
FALKORDB_VERSION = os.environ.get('FALKORDB_VERSION', 'v4.14.7')
```

**`build_scripts/update_redis_server.py`**:
```python
redis_version = os.environ.get('REDIS_VERSION', '8.2.2')
```

## Unified Version Strategy

All CI/CD jobs now use the same Redis and FalkorDB versions defined in `.versions.yml`. This ensures consistency across:
- Test jobs (Ubuntu and macOS)
- Build jobs (wheel creation)
- Publishing workflows

Previously, some jobs used different Redis versions, but this has been unified for simplicity and consistency.

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

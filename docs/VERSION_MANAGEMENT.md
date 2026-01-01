# Version Management

## Overview

The Redis and FalkorDB versions used in the falkordblite package are managed centrally in the `setup.cfg` file under the `[build_versions]` section.

## Configuration File

The `setup.cfg` file contains a `[build_versions]` section with simple `key = value` format:

```ini
[build_versions]
# Redis and FalkorDB versions used in building and testing
# This is the SINGLE SOURCE OF TRUTH for version management
redis_version = 8.2.2
falkordb_version = v4.14.11
```

## How Versions Are Used

### Python Build Scripts

The `setup.py` and `build_scripts/update_redis_server.py` scripts automatically read from `setup.cfg`:
- They parse the `[build_versions]` section using Python's `configparser`
- Environment variables can override these defaults: `REDIS_VERSION` and `FALKORDB_VERSION`
- **No fallback defaults**: Setup will fail if the `[build_versions]` section is missing or incomplete

### GitHub Actions Workflows

The CI/CD workflows (`.github/workflows/ci.yml` and `.github/workflows/publish.yml`) use the `.github/scripts/get_versions.sh` script to load versions:
- The script parses the `[build_versions]` section from `setup.cfg`
- Versions are exported as environment variables for use throughout the workflow
- **Script will fail** if required versions are not found

### Screwdriver CI

The `screwdriver.yaml` file reads the versions from `setup.cfg` during the build process.

## Updating Versions

To update the Redis or FalkorDB version:

1. Edit the `setup.cfg` file
2. Update the desired version(s) in the `[build_versions]` section
3. Commit the change

All build and CI systems will automatically use the new versions.

## Example

To update to Redis 8.2.3 and FalkorDB v4.15.0:

```bash
# Edit setup.cfg with your preferred editor
vim setup.cfg  # or nano, emacs, etc.

# Or use sed for automated updates
sed -i 's/redis_version = .*/redis_version = 8.2.3/' setup.cfg
sed -i 's/falkordb_version = .*/falkordb_version = v4.15.0/' setup.cfg

# Commit the change
git add setup.cfg
git commit -m "Update Redis to 8.2.3 and FalkorDB to v4.15.0"
```

## Design Decisions

### Why setup.cfg?

Using `setup.cfg` instead of a separate configuration file provides several benefits:
- **Single configuration file**: Reduces the number of files in the repository
- **Standard location**: `setup.cfg` is already used for package metadata
- **Built-in parser**: Python's `configparser` module provides robust parsing
- **No fallback defaults**: Setup explicitly fails if versions are not defined, preventing accidental builds with outdated versions


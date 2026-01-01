# Version Management

## Overview

The Redis and FalkorDB versions used in the falkordblite package are managed centrally in the `versions.txt` file located at the root of the repository.

## Configuration File

The `versions.txt` file uses a simple `KEY=VALUE` format:

```
REDIS_VERSION=8.2.2
FALKORDB_VERSION=v4.14.11
```

## How Versions Are Used

### Python Build Scripts

The `setup.py` and `build_scripts/update_redis_server.py` scripts automatically read from `versions.txt`:
- They parse the file to extract version information
- Environment variables can override these defaults: `REDIS_VERSION` and `FALKORDB_VERSION`
- Fallback defaults are provided if the file is not found

### GitHub Actions Workflows

The CI/CD workflows (`.github/workflows/ci.yml` and `.github/workflows/publish.yml`) use the `.github/scripts/get_versions.sh` script to load versions:
- The script sources the `versions.txt` file at the start of each job
- Versions are exported as environment variables for use throughout the workflow

### Screwdriver CI

The `screwdriver.yaml` file includes the versions in its environment configuration for compatibility with the Screwdriver CI system.

## Updating Versions

To update the Redis or FalkorDB version:

1. Edit the `versions.txt` file
2. Update the desired version(s)
3. Commit the change

All build and CI systems will automatically use the new versions.

## Example

To update to Redis 8.2.3 and FalkorDB v4.15.0:

```bash
# Edit versions.txt with your preferred editor
vim versions.txt  # or nano, emacs, etc.

# Or use sed for automated updates
sed -i 's/REDIS_VERSION=.*/REDIS_VERSION=8.2.3/' versions.txt
sed -i 's/FALKORDB_VERSION=.*/FALKORDB_VERSION=v4.15.0/' versions.txt

# Commit the change
git add versions.txt
git commit -m "Update Redis to 8.2.3 and FalkorDB to v4.15.0"
```

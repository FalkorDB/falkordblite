#!/usr/bin/env bash
# Script to read versions from setup.cfg and output them for GitHub Actions

set -e

# Get the repository root directory
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SETUP_CFG="${REPO_ROOT}/setup.cfg"

if [ ! -f "$SETUP_CFG" ]; then
    echo "Error: setup.cfg not found at $SETUP_CFG"
    exit 1
fi

# Read versions from [build_versions] section in setup.cfg
IN_BUILD_VERSIONS=0
while IFS='=' read -r key value; do
    # Detect [build_versions] section
    if [[ "$key" =~ ^\[build_versions\] ]]; then
        IN_BUILD_VERSIONS=1
        continue
    fi
    
    # Exit section if we hit another section header
    if [[ "$key" =~ ^\[.*\] ]]; then
        IN_BUILD_VERSIONS=0
        continue
    fi
    
    # Skip if not in build_versions section
    if [ $IN_BUILD_VERSIONS -eq 0 ]; then
        continue
    fi
    
    # Skip empty lines and comments
    [[ -z "$key" || "$key" =~ ^[[:space:]]*# ]] && continue
    
    # Trim whitespace using parameter expansion
    key="${key#"${key%%[![:space:]]*}"}"
    key="${key%"${key##*[![:space:]]}"}"
    value="${value#"${value%%[![:space:]]*}"}"
    value="${value%"${value##*[![:space:]]}"}"
    
    # Skip if key or value is empty after trimming
    [[ -z "$key" || -z "$value" ]] && continue
    
    # Convert to uppercase and add _VERSION suffix if not present
    if [[ "$key" == "redis_version" ]]; then
        ENV_KEY="REDIS_VERSION"
    elif [[ "$key" == "falkordb_version" ]]; then
        ENV_KEY="FALKORDB_VERSION"
    else
        echo "Warning: Ignoring unknown key '$key' from setup.cfg"
        continue
    fi
    
    # Export as environment variable
    export "$ENV_KEY=$value"
    
    # Output for GitHub Actions
    if [ -n "$GITHUB_ENV" ]; then
        echo "$ENV_KEY=$value" >> "$GITHUB_ENV"
    fi
    
    # Also output to stdout for debugging
    echo "$ENV_KEY=$value"
done < "$SETUP_CFG"

# Verify required versions were found
if [ -z "$REDIS_VERSION" ]; then
    echo "Error: redis_version not found in [build_versions] section of setup.cfg"
    exit 1
fi

if [ -z "$FALKORDB_VERSION" ]; then
    echo "Error: falkordb_version not found in [build_versions] section of setup.cfg"
    exit 1
fi

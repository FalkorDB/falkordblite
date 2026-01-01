#!/usr/bin/env bash
# Script to read versions from versions.txt and output them for GitHub Actions

set -e

# Get the repository root directory
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VERSIONS_FILE="${REPO_ROOT}/versions.txt"

if [ ! -f "$VERSIONS_FILE" ]; then
    echo "Error: versions.txt not found at $VERSIONS_FILE"
    exit 1
fi

# Whitelist of allowed variable names for security
ALLOWED_VARS=("REDIS_VERSION" "FALKORDB_VERSION")

# Read versions from file
while IFS='=' read -r key value; do
    # Skip empty lines and comments
    [[ -z "$key" || "$key" =~ ^[[:space:]]*# ]] && continue
    
    # Trim whitespace using parameter expansion
    key="${key#"${key%%[![:space:]]*}"}"
    key="${key%"${key##*[![:space:]]}"}"
    value="${value#"${value%%[![:space:]]*}"}"
    value="${value%"${value##*[![:space:]]}"}"
    
    # Validate key is in whitelist
    if [[ ! " ${ALLOWED_VARS[@]} " =~ " ${key} " ]]; then
        echo "Warning: Ignoring unknown variable '$key' from versions.txt"
        continue
    fi
    
    # Validate key contains only alphanumeric characters and underscores
    if [[ ! "$key" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then
        echo "Error: Invalid variable name '$key' in versions.txt"
        exit 1
    fi
    
    # Validate value doesn't contain shell metacharacters for security
    if [[ "$value" =~ [\$\`\;\\] ]]; then
        echo "Error: Value for '$key' contains invalid characters"
        exit 1
    fi
    
    # Export as environment variable
    export "$key=$value"
    
    # Output for GitHub Actions
    if [ -n "$GITHUB_ENV" ]; then
        echo "$key=$value" >> "$GITHUB_ENV"
    fi
    
    # Also output to stdout for debugging
    echo "$key=$value"
done < "$VERSIONS_FILE"

#!/bin/bash
# Script to read versions from versions.txt and output them for GitHub Actions

set -e

# Get the repository root directory
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VERSIONS_FILE="${REPO_ROOT}/versions.txt"

if [ ! -f "$VERSIONS_FILE" ]; then
    echo "Error: versions.txt not found at $VERSIONS_FILE"
    exit 1
fi

# Read versions from file
while IFS='=' read -r key value; do
    # Skip empty lines and comments
    [[ -z "$key" || "$key" =~ ^[[:space:]]*# ]] && continue
    
    # Trim whitespace
    key=$(echo "$key" | xargs)
    value=$(echo "$value" | xargs)
    
    # Export as environment variable
    export "$key=$value"
    
    # Output for GitHub Actions
    if [ -n "$GITHUB_ENV" ]; then
        echo "$key=$value" >> "$GITHUB_ENV"
    fi
    
    # Also output to stdout for debugging
    echo "$key=$value"
done < "$VERSIONS_FILE"

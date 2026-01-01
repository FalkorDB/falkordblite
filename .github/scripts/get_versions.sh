#!/usr/bin/env bash
# Script to read versions from setup.cfg and output them for GitHub Actions
# This script delegates to version_utils.py to avoid code duplication

set -e

# Get the repository root directory
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Use Python to read versions from setup.cfg
# This avoids duplicating the parsing logic between bash and Python
VERSIONS=$(python3 -c "
import sys
sys.path.insert(0, '${REPO_ROOT}')
try:
    from version_utils import read_versions_from_setup_cfg
    versions = read_versions_from_setup_cfg('${REPO_ROOT}/setup.cfg')
    for key, value in versions.items():
        print(f'{key}={value}')
except Exception as e:
    print(f'Error: {e}', file=sys.stderr)
    sys.exit(1)
")

# Check if Python script failed
if [ $? -ne 0 ]; then
    exit 1
fi

# Parse and export the versions
while IFS='=' read -r key value; do
    # Export as environment variable
    export "$key=$value"
    
    # Output for GitHub Actions
    if [ -n "$GITHUB_ENV" ]; then
        echo "$key=$value" >> "$GITHUB_ENV"
    fi
    
    # Also output to stdout for debugging
    echo "$key=$value"
done <<< "$VERSIONS"

#!/usr/bin/env python
# Copyright (c) 2025, FalkorDB
# Copyrights licensed under the New BSD License
# See the accompanying LICENSE.txt file for terms.
"""
Utility module for reading version configuration from versions.txt.

This module provides a single implementation of the version reading logic
that is used across setup.py, build scripts, and tests to ensure consistency.
"""
import os
import re


# Whitelist of allowed version keys for security
ALLOWED_VERSION_KEYS = {'REDIS_VERSION', 'FALKORDB_VERSION'}


def read_versions_file(versions_file_path=None):
    """
    Read Redis and FalkorDB versions from versions.txt.
    
    Args:
        versions_file_path (str, optional): Path to the versions.txt file.
            If not provided, assumes versions.txt is in the repository root.
    
    Returns:
        dict: Dictionary with version keys and values, e.g.,
            {'REDIS_VERSION': '8.2.2', 'FALKORDB_VERSION': 'v4.14.11'}
    
    Raises:
        ValueError: If the file contains invalid key names or values
    """
    versions = {}
    
    # If no path provided, try to find it relative to this file
    if versions_file_path is None:
        # This file is in the root, so versions.txt should be alongside it
        current_dir = os.path.dirname(os.path.abspath(__file__))
        versions_file_path = os.path.join(current_dir, 'versions.txt')
    
    if os.path.exists(versions_file_path):
        with open(versions_file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Validate key is in whitelist
                    if key not in ALLOWED_VERSION_KEYS:
                        # Log warning but don't fail for forward compatibility
                        continue
                    
                    # Validate key format (alphanumeric and underscores only)
                    if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', key):
                        raise ValueError(
                            f"Invalid key '{key}' on line {line_num} of {versions_file_path}"
                        )
                    
                    # Validate value doesn't contain potentially dangerous characters
                    # Allow: alphanumeric, dots, hyphens, and 'v' prefix for version tags
                    if not re.match(r'^[a-zA-Z0-9.\-v]+$', value):
                        raise ValueError(
                            f"Invalid value '{value}' for key '{key}' on line {line_num}"
                        )
                    
                    versions[key] = value
    
    return versions


def get_redis_version(versions_file_path=None, default='8.2.2'):
    """
    Get the Redis version from versions.txt or environment variable.
    
    Args:
        versions_file_path (str, optional): Path to the versions.txt file.
        default (str): Default version if not found.
    
    Returns:
        str: Redis version string.
    """
    versions = read_versions_file(versions_file_path)
    return os.environ.get('REDIS_VERSION', versions.get('REDIS_VERSION', default))


def get_falkordb_version(versions_file_path=None, default='v4.14.11'):
    """
    Get the FalkorDB version from versions.txt or environment variable.
    
    Args:
        versions_file_path (str, optional): Path to the versions.txt file.
        default (str): Default version if not found.
    
    Returns:
        str: FalkorDB version string.
    """
    versions = read_versions_file(versions_file_path)
    return os.environ.get('FALKORDB_VERSION', versions.get('FALKORDB_VERSION', default))


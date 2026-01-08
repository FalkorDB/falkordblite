#!/usr/bin/env python
# Copyright (c) 2025, FalkorDB
# Copyrights licensed under the New BSD License
# See the accompanying LICENSE.txt file for terms.
"""
Utility module for reading version configuration from setup.cfg.

This module provides a single implementation of the version reading logic
that is used across setup.py, build scripts, and tests to ensure consistency.
"""
import os
import configparser


def read_versions_from_setup_cfg(setup_cfg_path=None):
    """
    Read Redis and FalkorDB versions from setup.cfg [build_versions] section.
    
    Args:
        setup_cfg_path (str, optional): Path to the setup.cfg file.
            If not provided, assumes setup.cfg is in the repository root.
    
    Returns:
        dict: Dictionary with version keys and values, e.g.,
            {'REDIS_VERSION': '8.2.2', 'FALKORDB_VERSION': 'v4.14.11'}
    
    Raises:
        FileNotFoundError: If setup.cfg is not found
        ValueError: If the [build_versions] section or required keys are missing
    """
    # If no path provided, try to find it relative to this file
    if setup_cfg_path is None:
        # This file is in the root, so setup.cfg should be alongside it
        current_dir = os.path.dirname(os.path.abspath(__file__))
        setup_cfg_path = os.path.join(current_dir, 'setup.cfg')
    
    if not os.path.exists(setup_cfg_path):
        raise FileNotFoundError(f"setup.cfg not found at {setup_cfg_path}")
    
    config = configparser.ConfigParser()
    config.read(setup_cfg_path)
    
    if 'build_versions' not in config:
        raise ValueError(
            "Missing [build_versions] section in setup.cfg. "
            "This section must contain 'redis_version' and 'falkordb_version' keys."
        )
    
    build_versions = config['build_versions']
    
    # Convert to uppercase keys for consistency with environment variables
    versions = {}
    
    if 'redis_version' in build_versions:
        versions['REDIS_VERSION'] = build_versions['redis_version']
    else:
        raise ValueError("Missing 'redis_version' in [build_versions] section of setup.cfg")
    
    if 'falkordb_version' in build_versions:
        versions['FALKORDB_VERSION'] = build_versions['falkordb_version']
    else:
        raise ValueError("Missing 'falkordb_version' in [build_versions] section of setup.cfg")
    
    return versions


def get_redis_version(setup_cfg_path=None):
    """
    Get the Redis version from setup.cfg or environment variable.
    
    Environment variable REDIS_VERSION overrides the value in setup.cfg.
    
    Args:
        setup_cfg_path (str, optional): Path to the setup.cfg file.
    
    Returns:
        str: Redis version string.
    
    Raises:
        FileNotFoundError: If setup.cfg is not found
        ValueError: If required version keys are missing
    """
    # Environment variable takes precedence
    if 'REDIS_VERSION' in os.environ:
        return os.environ['REDIS_VERSION']
    
    versions = read_versions_from_setup_cfg(setup_cfg_path)
    return versions['REDIS_VERSION']


def get_falkordb_version(setup_cfg_path=None):
    """
    Get the FalkorDB version from setup.cfg or environment variable.
    
    Environment variable FALKORDB_VERSION overrides the value in setup.cfg.
    
    Args:
        setup_cfg_path (str, optional): Path to the setup.cfg file.
    
    Returns:
        str: FalkorDB version string.
    
    Raises:
        FileNotFoundError: If setup.cfg is not found
        ValueError: If required version keys are missing
    """
    # Environment variable takes precedence
    if 'FALKORDB_VERSION' in os.environ:
        return os.environ['FALKORDB_VERSION']
    
    versions = read_versions_from_setup_cfg(setup_cfg_path)
    return versions['FALKORDB_VERSION']


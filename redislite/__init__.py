# Copyright (c) 2015, Yahoo Inc.
# Copyrights licensed under the New BSD License
# See the accompanying LICENSE.txt file for terms.
"""
This module provides access to a redis server using a redis server embedded
in the module.  It provides enhanced redis bindings that are able to configure
run, and cleanup a redis server when they are accessed.

Attributes:
    __version__(str):
        The version of the redislite module.

    __redis_executable__(str):
        The full path to the embedded redis-server executable.

    __redis_server_version__(str):
        The version of the embedded redis-server built intot he module.

    __git_source_url__(str):
        The github web url for the source code used to generate this module.
        This will be an empty string if the module was not built from a github
        repo.

    __git_version__(str):
        Version number derived from the number of git revisions.
        This will be an empty string if not built from a git repo.

    __git_origin__(str):
        The git origin of the source repository the module was built from.
        This will be an empty string if not built from a git repo.

    __git_branch__(str):
        The git branch the module was built from.  This will be an empty string
        if not built from a git repo.

    __git_hash__(str):
        The git hash value for the code used to build this module.

Example:
  To access redis using a newly installed and configured redis server, then
  set and retrieve some data:

      >>> import redislite
      >>> connection = redislite.Redis()
      >>> connection.set('key', 'value')
      True
      >>> connection.get('key')
      'value'
      >>>
"""
import json
import os


__version__ = str('0.0.0')
__git_version__ = str("")
__git_origin__ = str("")
__git_branch__ = str("")
__git_hash__ = str("")
__source_url__ = str('')
__redis_server_info__ = {}
__redis_executable__ = str('')
__redis_server_version__ = str('')
__falkordb_module__ = str('')

try:
    # Use importlib.metadata instead of deprecated pkg_resources
    from importlib.metadata import version
    __git_version__ = version("redislite")
    __version__ = __git_version__
except (ImportError, Exception):  # pragma: no cover
    pass
    

_metadata_file = os.path.join(
    os.path.dirname(__file__),
    'package_metadata.json'
)


if os.path.exists(_metadata_file):  # pragma: no cover
    with open(_metadata_file) as fh:
        _package_metadata = json.load(fh)
        __git_origin__ = str(_package_metadata['git_origin'])
        __git_branch__ = str(_package_metadata['git_branch'])
        __git_hash__ = str(_package_metadata['git_hash'])
        __git_base_url__ = 'https://github.com/yahoo/redislite'
        if __git_origin__.endswith('.git'):  # pragma: no cover
            __git_base_url__ = __git_origin__[:-4].strip('/')
        __source_url__ = __git_base_url__ + '/tree/' + __git_hash__
        __redis_executable__ = str(_package_metadata['redis_bin'])
        __redis_server_info__ = _package_metadata['redis_server']
        __redis_server_version__ = __redis_server_info__.get('v', str(''))

# Auto-copy binaries from build directory for editable installs
def _ensure_binaries():
    """Ensure redis-server and falkordb.so are in redislite/bin/ for editable installs"""
    bin_dir = os.path.join(os.path.dirname(__file__), 'bin')
    
    # Check if binaries already exist
    if os.path.exists(os.path.join(bin_dir, 'redis-server')) and \
       os.path.exists(os.path.join(bin_dir, 'falkordb.so')):
        return  # All good
    
    # Try to find and copy from build directory
    base_dir = os.path.dirname(os.path.dirname(__file__))
    build_dirs = [
        os.path.join(base_dir, 'build', f'scripts-{v[0]}.{v[1]}') 
        for v in [(__import__('sys').version_info.major, __import__('sys').version_info.minor)]
    ]
    build_dirs.append(os.path.join(base_dir, 'build', 'scripts'))
    
    for build_dir in build_dirs:
        if not os.path.exists(build_dir):
            continue
        
        redis_server = os.path.join(build_dir, 'redis-server')
        falkordb_so = os.path.join(build_dir, 'falkordb.so')
        
        if os.path.exists(redis_server) and os.path.exists(falkordb_so):
            # Create bin directory
            if not os.path.exists(bin_dir):
                os.makedirs(bin_dir, 0o755)
            
            # Copy binaries
            import shutil
            for binary in ['redis-server', 'redis-cli', 'falkordb.so']:
                src = os.path.join(build_dir, binary)
                dst = os.path.join(bin_dir, binary)
                if os.path.exists(src) and not os.path.exists(dst):
                    shutil.copy2(src, dst)
                    os.chmod(dst, 0o755)
            break

try:
    _ensure_binaries()
except Exception:  # pragma: no cover
    pass  # Don't fail import if binary copy fails

if os.path.exists(os.path.join(os.path.dirname(__file__), "bin/redis-server")):
    __redis_executable__ = os.path.join(
        os.path.dirname(__file__),
        'bin/redis-server'
    )  # pragma: no cover

# Check for FalkorDB module in multiple locations
_falkordb_locations = [
    os.path.join(os.path.dirname(__file__), "bin/falkordb.so"),  # Installed location
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "falkordb.so"),  # Source/build location
]
for _location in _falkordb_locations:
    if os.path.exists(_location):
        __falkordb_module__ = _location
        break  # pragma: no cover

__all__ = [
    'client', 'configuration', 'debug', 'patch', 'falkordb_client',
    'async_client', 'async_falkordb_client'
]

from .client import Redis, StrictRedis  # NOQA
from .falkordb_client import FalkorDB, Graph  # NOQA
from .async_client import AsyncRedis, AsyncStrictRedis  # NOQA
from .async_falkordb_client import AsyncFalkorDB, AsyncGraph, AsyncQueryResult  # NOQA

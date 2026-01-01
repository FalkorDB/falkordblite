#!/usr/bin/env python3
""" Update the redis.submodule in the redislite repo to the latest stable version """
import os
import pathlib
import shutil
import urllib.request
import tarfile
import tempfile
import sys

# Add parent directory to path to import version_utils
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    from version_utils import get_redis_version
    redis_version = get_redis_version()
except ImportError:
    # Fallback to inline version reading if version_utils is not available
    def read_versions_file():
        """Read Redis and FalkorDB versions from versions.txt"""
        versions = {}
        versions_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'versions.txt')
        if os.path.exists(versions_file):
            with open(versions_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        versions[key.strip()] = value.strip()
        return versions

    _versions = read_versions_file()
    redis_version = os.environ.get('REDIS_VERSION', _versions.get('REDIS_VERSION', '8.2.2'))

url = f'https://download.redis.io/releases/redis-{redis_version}.tar.gz'


if __name__ == "__main__":
    if pathlib.Path('redis_submodule').exists():
        shutil.rmtree('redis.submodule')
    with tempfile.TemporaryDirectory() as tempdir:
        print(f'Downloading {url} to temp directory {tempdir}')
        ftpstream = urllib.request.urlopen(url)
        tf = tarfile.open(fileobj=ftpstream, mode="r|gz")
        directory = tf.next().name
        
        print(f'Extracting archive {directory}')
        tf.extractall(tempdir)
        
        print(f'Moving {os.path.join(tempdir, directory)} -> redis.submodule')
        shutil.move(os.path.join(tempdir, directory), 'redis.submodule')
        
        # print('Updating jemalloc')
        # os.system('(cd redis.submodule;./deps/update-jemalloc.sh 4.0.4)')
        
        # print('Adding new redis.submodule files to git')
        # os.system('git add redis.submodule')

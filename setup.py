#!/usr/bin/env python
# Copyright (c) 2015, Yahoo Inc.
# Copyrights licensed under the New BSD License
# See the accompanying LICENSE.txt file for terms.
from __future__ import print_function
import os
import json
import logging
import pathlib
import subprocess

from setuptools import setup
from setuptools.command.install import install
from setuptools.command.develop import develop
import shutil
import sys
import urllib.request
import tarfile
import tempfile
from distutils.command.build import build
from distutils.core import Extension
import distutils.util
from subprocess import call, check_output, CalledProcessError


logger = logging.getLogger(__name__)

UNSUPPORTED_PLATFORMS = ['win32', 'win64']
METADATA_FILENAME = 'redislite/package_metadata.json'
BASEPATH = os.path.dirname(os.path.abspath(__file__))
REDIS_PATH = os.path.join(BASEPATH, 'redis.submodule')
REDIS_SERVER_METADATA = {}
REDIS_VERSION = os.environ.get('REDIS_VERSION', '8.2.2')
REDIS_URL = f'http://download.redis.io/releases/redis-{REDIS_VERSION}.tar.gz'
FALKORDB_VERSION = os.environ.get('FALKORDB_VERSION', 'v4.14.2')
install_scripts = ''
try:
    VERSION = check_output(['meta', 'get', 'package.version']).decode(errors='ignore')
except (subprocess.CalledProcessError, FileNotFoundError):
    VERSION = REDIS_VERSION


def download_redis_submodule():
    if pathlib.Path(REDIS_PATH).exists():
        shutil.rmtree(REDIS_PATH)
    with tempfile.TemporaryDirectory() as tempdir:
        print(f'Downloading {REDIS_URL} to temp directory {tempdir}')
        ftpstream = urllib.request.urlopen(REDIS_URL)
        tf = tarfile.open(fileobj=ftpstream, mode="r|gz")
        directory = tf.next().name

        print(f'Extracting archive {directory}')
        tf.extractall(tempdir)

        print(f'Moving {os.path.join(tempdir, directory)} -> redis.submodule')
        shutil.move(os.path.join(tempdir, directory), 'redis.submodule')

        # print('Updating jemalloc')
        # os.system('(cd redis.submodule;./deps/update-jemalloc.sh 4.0.4)')


def download_and_build_falkordb():
    """Clone and build FalkorDB module from source"""
    falkordb_path = os.path.join(BASEPATH, 'FalkorDB')
    
    # Remove existing FalkorDB directory if present
    if pathlib.Path(falkordb_path).exists():
        shutil.rmtree(falkordb_path)
    
    # Clone FalkorDB repository with submodules
    print(f'Cloning FalkorDB {FALKORDB_VERSION}...')
    try:
        result = call([
            'git', 'clone', '--depth', '1', '--recursive',
            '--branch', FALKORDB_VERSION,
            'https://github.com/FalkorDB/FalkorDB.git',
            falkordb_path
        ])
        if result != 0:
            raise Exception(f'Git clone failed with exit code {result}')
        print(f'FalkorDB cloned to {falkordb_path}')
    except Exception as e:
        print(f'Failed to clone FalkorDB: {e}')
        raise
    
    # Build FalkorDB module
    print('Building FalkorDB module...')
    print('*' * 80)
    
    try:
        # Run make in the FalkorDB directory
        print('Running make...')
        result = call(['make'], cwd=falkordb_path)
        if result != 0:
            raise Exception(f'FalkorDB build failed with exit code {result}')
        
        # Copy the built module to the base path
        built_module = os.path.join(falkordb_path, 'bin', 'linux-x64-release', 'src', 'falkordb.so')
        dest_module = os.path.join(BASEPATH, 'falkordb.so')
        
        if os.path.exists(built_module):
            shutil.copy2(built_module, dest_module)
            print(f'FalkorDB module built and copied to {dest_module}')
        else:
            raise Exception(f'Built module not found at {built_module}')
            
    except Exception as e:
        print(f'Failed to build FalkorDB module: {e}')
        raise
    finally:
        print('*' * 80)


class BuildRedis(build):
    global REDIS_SERVER_METADATA

    def _copy_binaries_to_source(self):
        """Copy built binaries to redislite/bin/ in the source directory for editable installs"""
        if not self.build_scripts or not os.path.exists(self.build_scripts):
            logger.warning('Build scripts directory not found, skipping binary copy to source')
            return
        
        # Create redislite/bin in the source directory
        source_bin = os.path.join(BASEPATH, 'redislite', 'bin')
        if not os.path.exists(source_bin):
            os.makedirs(source_bin, 0o0755)
            logger.debug('Created directory: %s', source_bin)
        
        binaries = ['redis-server', 'redis-cli', 'falkordb.so']
        
        for binary in binaries:
            src = os.path.join(self.build_scripts, binary)
            dst = os.path.join(source_bin, binary)
            if os.path.exists(src):
                shutil.copy2(src, dst)
                os.chmod(dst, 0o755)
                logger.debug('Copied and set permissions: %s -> %s', src, dst)
        
        print('*' * 80)
        print('Binaries copied to redislite/bin/ for editable install')
        print(f'  Location: {source_bin}')
        print('*' * 80)

    def run(self):
        # run original build code
        build.run(self)

        # build Redis
        logger.debug('Running build_redis')

        os.environ['CC'] = 'gcc'
        os.environ['PREFIX'] = REDIS_PATH
        cmd = [
            'make',
            'MALLOC=libc',
            'V=' + str(self.verbose),
        ]

        targets = ['install']
        cmd.extend(targets)

        target_files = [
            os.path.join(REDIS_PATH, 'bin/redis-server'),
            os.path.join(REDIS_PATH, 'bin/redis-cli'),
        ]

        def _compile():
            print('*' * 80)
            print(os.getcwd())
            call(cmd, cwd=REDIS_PATH)
            print('*' * 80)

        self.execute(_compile, [], 'compiling redis')

        # copy resulting tool to script folder
        self.mkpath(self.build_scripts)

        if not self.dry_run:
            for target in target_files:
                logger.debug('copy: %s -> %s', target, self.build_scripts)
                self.copy_file(target, self.build_scripts)
            
            # Copy FalkorDB module if it exists
            falkordb_module = os.path.join(BASEPATH, 'falkordb.so')
            if os.path.exists(falkordb_module):
                logger.debug('copy: %s -> %s', falkordb_module, self.build_scripts)
                self.copy_file(falkordb_module, self.build_scripts)
                # Set executable permissions on the FalkorDB module
                dest_falkordb = os.path.join(self.build_scripts, 'falkordb.so')
                os.chmod(dest_falkordb, 0o755)
                logger.debug('Set executable permissions on %s', dest_falkordb)
            
            # Also copy binaries to source directory for editable installs
            self._copy_binaries_to_source()


class PostBuildCopyBinaries:
    """Mixin to copy binaries to redislite/bin/ for editable installs"""
    
    def copy_binaries_to_source(self):
        """Copy built binaries to redislite/bin/ in the source directory"""
        # Determine the build_scripts directory
        build_cmd = self.get_finalized_command('build')
        build_scripts = build_cmd.build_scripts
        
        if not build_scripts or not os.path.exists(build_scripts):
            logger.warning('Build scripts directory not found, skipping binary copy')
            return
        
        # Create redislite/bin in the source directory
        source_bin = os.path.join(BASEPATH, 'redislite', 'bin')
        if not os.path.exists(source_bin):
            os.makedirs(source_bin, 0o0755)
            logger.debug('Created directory: %s', source_bin)
        
        # Copy redis-server
        redis_server_src = os.path.join(build_scripts, 'redis-server')
        redis_server_dst = os.path.join(source_bin, 'redis-server')
        if os.path.exists(redis_server_src):
            shutil.copy2(redis_server_src, redis_server_dst)
            os.chmod(redis_server_dst, 0o755)
            logger.debug('Copied and set permissions: %s -> %s', redis_server_src, redis_server_dst)
        
        # Copy redis-cli
        redis_cli_src = os.path.join(build_scripts, 'redis-cli')
        redis_cli_dst = os.path.join(source_bin, 'redis-cli')
        if os.path.exists(redis_cli_src):
            shutil.copy2(redis_cli_src, redis_cli_dst)
            os.chmod(redis_cli_dst, 0o755)
            logger.debug('Copied and set permissions: %s -> %s', redis_cli_src, redis_cli_dst)
        
        # Copy FalkorDB module
        falkordb_src = os.path.join(build_scripts, 'falkordb.so')
        falkordb_dst = os.path.join(source_bin, 'falkordb.so')
        if os.path.exists(falkordb_src):
            shutil.copy2(falkordb_src, falkordb_dst)
            os.chmod(falkordb_dst, 0o755)
            logger.debug('Copied and set permissions: %s -> %s', falkordb_src, falkordb_dst)
        
        print('*' * 80)
        print('Binaries copied to redislite/bin/ for editable install')
        print(f'  redis-server: {redis_server_dst}')
        print(f'  redis-cli: {redis_cli_dst}')
        print(f'  falkordb.so: {falkordb_dst}')
        print('*' * 80)


class DevelopRedis(PostBuildCopyBinaries, develop):
    """Custom develop command for editable installs"""
    
    def run(self):
        # Run the standard develop installation
        develop.run(self)
        
        # Copy binaries to source directory for editable installs
        self.copy_binaries_to_source()


class InstallRedis(install):
    build_scripts = None

    def initialize_options(self):
        install.initialize_options(self)

    def finalize_options(self):
        install.finalize_options(self)
        self.set_undefined_options('build', ('build_scripts', 'build_scripts'))

    def run(self):
        global install_scripts
        # run original install code
        install.run(self)

        # install Redis executables
        logger.debug(
            'running InstallRedis %s -> %s', self.build_lib, self.install_lib
        )
        self.copy_tree(self.build_lib, self.install_lib)
        module_bin = os.path.join(self.install_lib, 'redislite/bin')
        if not os.path.exists(module_bin):
            os.makedirs(module_bin, 0o0755)
        self.copy_tree(self.build_scripts, module_bin)
        logger.debug(
            'running InstallRedis %s -> %s',
            self.build_scripts, self.install_scripts
        )
        self.copy_tree(self.build_scripts, self.install_scripts)

        # Set executable permissions on FalkorDB module after installation
        for install_dir in [module_bin, self.install_scripts]:
            falkordb_path = os.path.join(install_dir, 'falkordb.so')
            if os.path.exists(falkordb_path):
                os.chmod(falkordb_path, 0o755)
                logger.debug('Set executable permissions on %s', falkordb_path)

        install_scripts = self.install_scripts
        print('install_scripts: %s' % install_scripts)
        md_file = os.path.join(
            self.install_lib, 'redislite/package_metadata.json'
        )
        if os.path.exists(md_file):
            with open(md_file) as fh:
                md = json.load(fh)
                if os.path.exists(os.path.join(module_bin, 'redis-server')):
                    md['redis_bin'] = os.path.join(module_bin, 'redis-server')
                else:
                    md['redis_bin'] = os.path.join(
                        install_scripts, 'redis-server'
                    )
            # Store the redis-server --version output for later
            for line in os.popen('%s --version' % md['redis_bin']).readlines():
                line = line.strip()
                for item in line.split():
                    if '=' in item:
                        key, value = item.split('=')
                        REDIS_SERVER_METADATA[key] = value
            md['redis_server'] = REDIS_SERVER_METADATA
            print('new metadata: %s' % md)
            with open(md_file, 'w') as fh:
                json.dump(md, fh, indent=4)

# Create a dictionary of our arguments, this way this script can be imported
#  without running setup() to allow external scripts to see the setup settings.
args = {
    'package_data': {
        'redislite': ['package_metadata.json', 'bin/redis-server', 'bin/falkordb.so'],
    },
    'include_package_data': True,
    'cmdclass': {
        'build': BuildRedis,
        'install': InstallRedis,
        'develop': DevelopRedis,
    },

    # We put in a bogus extension module so wheel knows this package has
    # compiled components.
    'ext_modules': [
        Extension('dummy', sources=['src/dummy.c'])
    ],
    # 'extras_require': {
    #     ':sys_platform=="darwin"': [],
    #     ':sys_platform=="linux"': [],
    # }
}
setup_arguments = args

# Add any scripts we want to package
if os.path.isdir('scripts'):
    setup_arguments['scripts'] = [
        os.path.join('scripts', f) for f in os.listdir('scripts')
    ]


class Git(object):
    version_list = ['0', '7', '0']

    def __init__(self, version=None):
        if version:
            self.version_list = version.split('.')

    @property
    def version(self):
        """
        Generate a Unique version value from the git information
        :return:
        """
        git_rev = len(os.popen('git rev-list HEAD').readlines())
        if git_rev != 0:
            self.version_list[-1] = '%d' % git_rev
        version = '.'.join(self.version_list)
        return version

    @property
    def branch(self):
        """
        Get the current git branch
        :return:
        """
        return os.popen('git rev-parse --abbrev-ref HEAD').read().strip()

    @property
    def hash(self):
        """
        Return the git hash for the current build
        :return:
        """
        return os.popen('git rev-parse HEAD').read().strip()

    @property
    def origin(self):
        """
        Return the fetch url for the git origin
        :return:
        """
        for item in os.popen('git remote -v'):
            split_item = item.strip().split()
            if split_item[0] == 'origin' and split_item[-1] == '(push)':
                return split_item[1]


def get_and_update_metadata():
    """
    Get the package metadata or generate it if missing
    :return:
    """
    global METADATA_FILENAME
    global REDIS_SERVER_METADATA

    if not os.path.exists('.git') and os.path.exists(METADATA_FILENAME):
        with open(METADATA_FILENAME) as fh:
            metadata = json.load(fh)
    else:
        git = Git(version=VERSION)
        metadata = {
            'git_origin': git.origin,
            'git_branch': git.branch,
            'git_hash': git.hash,
            'redis_server': REDIS_SERVER_METADATA,
            'redis_bin': install_scripts
        }
        with open(METADATA_FILENAME, 'w') as fh:
            json.dump(metadata, fh, indent=4)
    return metadata


if __name__ == '__main__':
    if sys.platform in UNSUPPORTED_PLATFORMS:
        print(
            'The redislite module is not supported on the %r '
            'platform' % sys.platform,
            file=sys.stderr
        )
        sys.exit(1)

    os.environ['CC'] = 'gcc'

    logging.basicConfig(level=logging.DEBUG)

    if not os.path.exists(REDIS_PATH):
        logger.debug(f'Downloading redis version {REDIS_VERSION}')
        download_redis_submodule()
    
    # Build FalkorDB module if not present
    falkordb_module = os.path.join(BASEPATH, 'falkordb.so')
    if not os.path.exists(falkordb_module):
        logger.debug(f'Building FalkorDB version {FALKORDB_VERSION}')
        download_and_build_falkordb()

    logger.debug('Building for platform: %s', distutils.util.get_platform())

    metadata = get_and_update_metadata()

    setup(**setup_arguments)

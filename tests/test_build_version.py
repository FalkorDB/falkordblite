# Copyright (c) 2024, FalkorDB
# Copyrights licensed under the New BSD License
# See the accompanying LICENSE.txt file for terms.
"""Tests for FalkorDB build-time version selection."""
import importlib.util
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


def load_setup():
    spec = importlib.util.spec_from_file_location(
        'falkordblite_setup', Path(__file__).resolve().parents[1] / 'setup.py'
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestFalkorDBBuildVersion(unittest.TestCase):
    def test_cached_artifacts_with_different_versions_are_refreshed(self):
        setup = load_setup()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            redis_path = root / 'redis.submodule'
            redis_path.mkdir()
            (redis_path / 'FALKORDBLITE_VERSION').write_text('old\n', encoding='utf-8')
            module_path = root / 'falkordb.so'
            module_path.write_bytes(b'old module')
            (root / 'falkordb.version').write_text('old\n', encoding='utf-8')

            def refresh_redis():
                (redis_path / 'FALKORDBLITE_VERSION').write_text(
                    setup.REDIS_VERSION + '\n', encoding='utf-8'
                )

            def refresh_falkordb():
                module_path.write_bytes(b'new module')
                (root / 'falkordb.version').write_text(
                    setup.FALKORDB_VERSION + '\n', encoding='utf-8'
                )

            with patch.object(setup, 'BASEPATH', directory), \
                    patch.object(setup, 'REDIS_PATH', str(redis_path)), \
                    patch.object(setup, 'download_redis_submodule', side_effect=refresh_redis) as redis, \
                    patch.object(setup, 'download_falkordb_module', side_effect=refresh_falkordb) as falkordb:
                setup.ensure_build_sources()

            redis.assert_called_once_with()
            falkordb.assert_called_once_with()
            self.assertEqual(module_path.read_bytes(), b'new module')

    def test_matching_cached_artifacts_are_reused(self):
        setup = load_setup()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            redis_path = root / 'redis.submodule'
            redis_path.mkdir()
            (redis_path / 'FALKORDBLITE_VERSION').write_text(
                setup.REDIS_VERSION + '\n', encoding='utf-8'
            )
            module_path = root / 'falkordb.so'
            module_path.write_bytes(b'module')
            (root / 'falkordb.version').write_text(
                setup.FALKORDB_VERSION + '\n', encoding='utf-8'
            )

            with patch.object(setup, 'BASEPATH', directory), \
                    patch.object(setup, 'REDIS_PATH', str(redis_path)), \
                    patch.object(setup, 'download_redis_submodule') as redis, \
                    patch.object(setup, 'download_falkordb_module') as falkordb:
                setup.ensure_build_sources()

            redis.assert_not_called()
            falkordb.assert_not_called()

    def test_prerelease_tag_uses_recorded_source_tag_not_version_header(self):
        with patch.dict(os.environ, {'REDIS_VERSION': '8.0-rc1'}, clear=True):
            setup = load_setup()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            redis_path = root / 'redis.submodule'
            redis_path.mkdir()
            (redis_path / 'FALKORDBLITE_VERSION').write_text('8.0-rc1\n', encoding='utf-8')
            (redis_path / 'src').mkdir()
            (redis_path / 'src' / 'version.h').write_text(
                '#define REDIS_VERSION "7.9.240"\n', encoding='utf-8'
            )
            (root / 'falkordb.so').write_bytes(b'module')
            (root / 'falkordb.version').write_text(
                setup.FALKORDB_VERSION + '\n', encoding='utf-8'
            )

            with patch.object(setup, 'BASEPATH', directory), \
                    patch.object(setup, 'REDIS_PATH', str(redis_path)), \
                    patch.object(setup, 'download_redis_submodule') as redis:
                setup.ensure_build_sources()

            redis.assert_not_called()

    def test_failed_module_refresh_invalidates_old_version_marker(self):
        setup = load_setup()
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / 'falkordb.version'
            marker.write_text('old\n', encoding='utf-8')
            with patch.object(setup, 'BASEPATH', directory), \
                    patch.object(setup, 'get_ssl_context', return_value=None), \
                    patch('platform.system', return_value='Linux'), \
                    patch('platform.machine', return_value='x86_64'), \
                    patch.object(setup.urllib.request, 'urlopen', side_effect=OSError('download failed')):
                with self.assertRaises(OSError):
                    setup.download_falkordb_module()
            self.assertFalse(marker.exists())

    def test_notice_uses_the_selected_source_tags(self):
        overrides = {'REDIS_VERSION': '8-test', 'FALKORDB_VERSION': 'v-test'}
        for env in ({}, overrides):
            with self.subTest(env=env), patch.dict(os.environ, env, clear=True), \
                    tempfile.TemporaryDirectory() as directory:
                setup = load_setup()
                repo_notice = Path(setup.BASEPATH) / 'NOTICE'
                versions = setup._read_versions_cfg() | env
                with patch.object(setup, 'BASEPATH', directory):
                    setup.write_license_notice()
                notice = (Path(directory) / 'NOTICE').read_text(encoding='utf-8')
                redis = versions['REDIS_VERSION']
                falkordb = versions['FALKORDB_VERSION']
                self.assertIn(f'Source: https://github.com/redis/redis/tree/{redis}\n', notice)
                self.assertIn(f'Source: https://github.com/FalkorDB/FalkorDB/tree/{falkordb}\n', notice)
                self.assertIn(f'https://github.com/FalkorDB/FalkorDB/tree/{falkordb}/deps\n', notice)
                if not env:
                    self.assertEqual(notice, repo_notice.read_text(encoding='utf-8'))

    def test_selected_version_is_used_on_all_platforms(self):
        platforms = (
            ('Darwin', 'arm64', 'falkordb-macos-arm64v8.so'),
            ('Linux', 'x86_64', 'falkordb-x64.so'),
            ('Linux', 'aarch64', 'falkordb-arm64v8.so'),
        )
        for override in (None, 'v-test'):
            with self.subTest(override=override), patch.dict(
                os.environ, {'FALKORDB_VERSION': override} if override else {}, clear=True
            ):
                setup = load_setup()
                version = override or setup._read_versions_cfg()['FALKORDB_VERSION']
                for system, machine, asset in platforms:
                    with self.subTest(system=system, machine=machine), \
                            tempfile.TemporaryDirectory() as directory, \
                            patch('platform.system', return_value=system), \
                            patch('platform.machine', return_value=machine), \
                            patch.object(setup, 'BASEPATH', directory), \
                            patch.object(setup, 'get_ssl_context', return_value=None), \
                            patch.object(setup.urllib.request, 'urlopen', return_value=io.BytesIO(b'module')) as urlopen:
                        setup.download_falkordb_module()
                        urlopen.assert_called_once_with(
                            f'https://github.com/FalkorDB/FalkorDB/releases/download/{version}/{asset}',
                            context=None,
                        )
                        self.assertEqual((Path(directory) / 'falkordb.so').read_bytes(), b'module')

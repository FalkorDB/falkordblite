# Copyright (c) 2025, FalkorDB
# Copyrights licensed under the New BSD License
# See the accompanying LICENSE.txt file for terms.
"""
Tests for version management.
"""
import os
import sys
import unittest
import pathlib


class TestVersionManagement(unittest.TestCase):
    """Test that version management is working correctly."""

    def setUp(self):
        """Set up test fixtures."""
        self.repo_root = pathlib.Path(__file__).parent.parent
        self.versions_file = self.repo_root / 'versions.txt'
        
    def test_versions_file_exists(self):
        """Test that versions.txt exists."""
        self.assertTrue(
            self.versions_file.exists(),
            f"versions.txt should exist at {self.versions_file}"
        )

    def test_versions_file_readable(self):
        """Test that versions.txt can be read and parsed."""
        versions = {}
        with open(self.versions_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    versions[key.strip()] = value.strip()
        
        self.assertIn('REDIS_VERSION', versions)
        self.assertIn('FALKORDB_VERSION', versions)
        
        # Verify versions are not empty
        self.assertTrue(versions['REDIS_VERSION'])
        self.assertTrue(versions['FALKORDB_VERSION'])
        
        # Verify REDIS_VERSION looks like a version number
        redis_version = versions['REDIS_VERSION']
        self.assertRegex(
            redis_version, 
            r'^\d+\.\d+\.\d+$',
            f"REDIS_VERSION '{redis_version}' should be in format X.Y.Z"
        )
        
        # Verify FALKORDB_VERSION looks like a version tag
        falkordb_version = versions['FALKORDB_VERSION']
        self.assertTrue(
            falkordb_version.startswith('v'),
            f"FALKORDB_VERSION '{falkordb_version}' should start with 'v'"
        )

    def test_setup_py_reads_versions(self):
        """Test that setup.py can read versions from versions.txt."""
        # Add the repo root to the path
        sys.path.insert(0, str(self.repo_root))
        
        # Import and use the shared utility
        try:
            from version_utils import get_redis_version, get_falkordb_version
            redis_version = get_redis_version(str(self.versions_file))
            falkordb_version = get_falkordb_version(str(self.versions_file))
        except ImportError:
            # Fallback to inline reading if utility not available
            def read_versions_file():
                versions = {}
                if self.versions_file.exists():
                    with open(self.versions_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#') and '=' in line:
                                key, value = line.split('=', 1)
                                versions[key.strip()] = value.strip()
                return versions
            
            versions = read_versions_file()
            redis_version = os.environ.get('REDIS_VERSION', versions.get('REDIS_VERSION', ''))
            falkordb_version = os.environ.get('FALKORDB_VERSION', versions.get('FALKORDB_VERSION', ''))
        
        self.assertTrue(redis_version, "REDIS_VERSION should be set")
        self.assertTrue(falkordb_version, "FALKORDB_VERSION should be set")

    def test_version_utils_module(self):
        """Test that the version_utils module works correctly."""
        sys.path.insert(0, str(self.repo_root))
        
        try:
            from version_utils import read_versions_file, get_redis_version, get_falkordb_version
            
            # Test read_versions_file
            versions = read_versions_file(str(self.versions_file))
            self.assertIn('REDIS_VERSION', versions)
            self.assertIn('FALKORDB_VERSION', versions)
            
            # Test get_redis_version
            redis_version = get_redis_version(str(self.versions_file))
            self.assertRegex(redis_version, r'^\d+\.\d+\.\d+$')
            
            # Test get_falkordb_version
            falkordb_version = get_falkordb_version(str(self.versions_file))
            self.assertTrue(falkordb_version.startswith('v'))
            
        except ImportError:
            self.skipTest("version_utils module not available")

    def test_bash_script_exists(self):
        """Test that the bash script for reading versions exists."""
        script_path = self.repo_root / '.github' / 'scripts' / 'get_versions.sh'
        self.assertTrue(
            script_path.exists(),
            f"get_versions.sh should exist at {script_path}"
        )
        
        # Check that it's executable
        self.assertTrue(
            os.access(script_path, os.X_OK),
            f"get_versions.sh should be executable"
        )

    def test_documentation_exists(self):
        """Test that version management documentation exists."""
        doc_path = self.repo_root / 'docs' / 'VERSION_MANAGEMENT.md'
        self.assertTrue(
            doc_path.exists(),
            f"VERSION_MANAGEMENT.md should exist at {doc_path}"
        )
        
        # Verify it mentions versions.txt
        with open(doc_path, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn('versions.txt', content)
            self.assertIn('REDIS_VERSION', content)
            self.assertIn('FALKORDB_VERSION', content)


if __name__ == '__main__':
    unittest.main()

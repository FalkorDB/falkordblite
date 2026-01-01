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
import configparser


class TestVersionManagement(unittest.TestCase):
    """Test that version management is working correctly."""

    def setUp(self):
        """Set up test fixtures."""
        self.repo_root = pathlib.Path(__file__).parent.parent
        self.setup_cfg_file = self.repo_root / 'setup.cfg'
        
    def test_setup_cfg_exists(self):
        """Test that setup.cfg exists."""
        self.assertTrue(
            self.setup_cfg_file.exists(),
            f"setup.cfg should exist at {self.setup_cfg_file}"
        )

    def test_build_versions_section_readable(self):
        """Test that setup.cfg [build_versions] section can be read and parsed."""
        config = configparser.ConfigParser()
        config.read(self.setup_cfg_file)
        
        self.assertIn('build_versions', config.sections(),
                     "[build_versions] section should exist in setup.cfg")
        
        build_versions = config['build_versions']
        self.assertIn('redis_version', build_versions,
                     "redis_version should be in [build_versions]")
        self.assertIn('falkordb_version', build_versions,
                     "falkordb_version should be in [build_versions]")
        
        # Verify versions are not empty
        redis_version = build_versions['redis_version']
        falkordb_version = build_versions['falkordb_version']
        
        self.assertTrue(redis_version, "redis_version should not be empty")
        self.assertTrue(falkordb_version, "falkordb_version should not be empty")
        
        # Verify redis_version looks like a version number
        self.assertRegex(
            redis_version, 
            r'^\d+\.\d+\.\d+$',
            f"redis_version '{redis_version}' should be in format X.Y.Z"
        )
        
        # Verify falkordb_version looks like a version tag
        self.assertTrue(
            falkordb_version.startswith('v'),
            f"falkordb_version '{falkordb_version}' should start with 'v'"
        )

    def test_setup_py_reads_versions(self):
        """Test that setup.py can read versions from setup.cfg."""
        # Add the repo root to the path
        sys.path.insert(0, str(self.repo_root))
        
        # Import and use the shared utility
        try:
            from version_utils import get_redis_version, get_falkordb_version
            redis_version = get_redis_version(str(self.setup_cfg_file))
            falkordb_version = get_falkordb_version(str(self.setup_cfg_file))
            
            self.assertTrue(redis_version, "REDIS_VERSION should be set")
            self.assertTrue(falkordb_version, "FALKORDB_VERSION should be set")
        except ImportError:
            self.skipTest("version_utils module not available")

    def test_version_utils_module(self):
        """Test that the version_utils module works correctly."""
        sys.path.insert(0, str(self.repo_root))
        
        try:
            from version_utils import read_versions_from_setup_cfg, get_redis_version, get_falkordb_version
            
            # Test read_versions_from_setup_cfg
            versions = read_versions_from_setup_cfg(str(self.setup_cfg_file))
            self.assertIn('REDIS_VERSION', versions)
            self.assertIn('FALKORDB_VERSION', versions)
            
            # Test get_redis_version
            redis_version = get_redis_version(str(self.setup_cfg_file))
            self.assertRegex(redis_version, r'^\d+\.\d+\.\d+$')
            
            # Test get_falkordb_version
            falkordb_version = get_falkordb_version(str(self.setup_cfg_file))
            self.assertTrue(falkordb_version.startswith('v'))
            
        except ImportError:
            self.skipTest("version_utils module not available")

    def test_version_utils_fails_without_setup_cfg(self):
        """Test that version_utils raises appropriate errors when setup.cfg is missing."""
        sys.path.insert(0, str(self.repo_root))
        
        try:
            from version_utils import get_redis_version
            import tempfile
            
            # Test that missing file raises FileNotFoundError
            with tempfile.TemporaryDirectory() as tmpdir:
                nonexistent_cfg = os.path.join(tmpdir, 'nonexistent.cfg')
                with self.assertRaises(FileNotFoundError):
                    get_redis_version(nonexistent_cfg)
                    
        except ImportError:
            self.skipTest("version_utils module not available")

    def test_version_utils_fails_without_build_versions_section(self):
        """Test that version_utils raises appropriate errors when [build_versions] section is missing."""
        sys.path.insert(0, str(self.repo_root))
        
        try:
            from version_utils import get_redis_version
            import tempfile
            
            # Test that missing section raises ValueError
            with tempfile.NamedTemporaryFile(mode='w', suffix='.cfg', delete=False) as f:
                f.write("[metadata]\nname = test\n")
                temp_file = f.name
            
            try:
                with self.assertRaises(ValueError) as context:
                    get_redis_version(temp_file)
                self.assertIn("[build_versions]", str(context.exception))
            finally:
                os.unlink(temp_file)
                
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
        
        # Verify it mentions setup.cfg
        with open(doc_path, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn('setup.cfg', content)
            self.assertIn('redis_version', content.lower())
            self.assertIn('falkordb_version', content.lower())


if __name__ == '__main__':
    unittest.main()

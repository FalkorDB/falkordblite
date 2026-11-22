# Copyright (c) 2015, Yahoo Inc.
# Copyrights licensed under the New BSD License
# See the accompanying LICENSE.txt file for terms.
"""
Tests for `redislite` module (__init__.py).
"""
from __future__ import print_function
import importlib
from importlib.metadata import PackageNotFoundError
import logging
import redislite
import redislite.patch
import unittest
from unittest.mock import patch


logger = logging.getLogger(__name__)


# noinspection PyPep8Naming
class TestRedisliteModule(unittest.TestCase):
    def test_version_uses_falkordblite_distribution(self):
        try:
            with patch('importlib.metadata.version', return_value='1.2.3') as version:
                importlib.reload(redislite)
                version.assert_called_once_with('falkordblite')
                self.assertEqual(redislite.__version__, '1.2.3')
                self.assertEqual(redislite.__git_version__, '1.2.3')
        finally:
            importlib.reload(redislite)

    def test_version_without_installed_distribution(self):
        try:
            with patch('importlib.metadata.version', side_effect=PackageNotFoundError):
                importlib.reload(redislite)
                self.assertEqual(redislite.__version__, '0.0.0')
        finally:
            importlib.reload(redislite)

    def test_metadata(self):
        self.assertIsInstance(redislite.__version__, str)
        self.assertIsInstance(redislite.__git_version__, str)
        self.assertIsInstance(redislite.__git_origin__, str)
        self.assertIsInstance(redislite.__git_branch__, str)
        self.assertIsInstance(redislite.__git_hash__, str)
        self.assertIsInstance(redislite.__redis_server_info__, dict)
        self.assertIsInstance(redislite.__redis_executable__, str)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    test_suite = unittest.TestLoader().loadTestsFromTestCase(
        TestRedisliteModule
    )
    unittest.TextTestRunner(verbosity=2).run(test_suite)

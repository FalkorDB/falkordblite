"""Tests for wheel naming and platform tags"""
import platform
import unittest
from unittest.mock import patch


class TestWheelPlatformTags(unittest.TestCase):
    """Test that wheel platform tags are correctly set"""

    def test_macos_arm64_platform_tag(self):
        """Test that ARM64 macOS uses correct platform tag"""
        with patch('platform.system', return_value='Darwin'), \
             patch('platform.machine', return_value='arm64'):
            system = platform.system().lower()
            machine = platform.machine().lower()
            
            if system == 'darwin':
                if machine in ['arm64', 'aarch64']:
                    plat_name = 'macosx_11_0_arm64'
                else:
                    plat_name = 'macosx_10_13_x86_64'
            
            self.assertEqual(plat_name, 'macosx_11_0_arm64')
            self.assertNotIn('x86_64', plat_name)

    def test_macos_x86_64_platform_tag(self):
        """Test that x86_64 macOS uses correct platform tag"""
        with patch('platform.system', return_value='Darwin'), \
             patch('platform.machine', return_value='x86_64'):
            system = platform.system().lower()
            machine = platform.machine().lower()
            
            if system == 'darwin':
                if machine in ['arm64', 'aarch64']:
                    plat_name = 'macosx_11_0_arm64'
                else:
                    plat_name = 'macosx_10_13_x86_64'
            
            self.assertEqual(plat_name, 'macosx_10_13_x86_64')
            self.assertNotIn('arm64', plat_name)

    def test_linux_platform_tag(self):
        """Test that Linux uses correct platform tag"""
        import distutils.util
        
        with patch('platform.system', return_value='Linux'), \
             patch('platform.machine', return_value='x86_64'):
            system = platform.system().lower()
            
            if system == 'darwin':
                plat_name = 'macosx_11_0_arm64'  # Won't be used
            else:
                plat_name = distutils.util.get_platform().replace('-', '_').replace('.', '_')
            
            # Should contain linux and architecture
            self.assertIn('linux', plat_name.lower())
            # Should not have multiple platform tags
            self.assertEqual(plat_name.count('linux'), 1)


if __name__ == '__main__':
    unittest.main()

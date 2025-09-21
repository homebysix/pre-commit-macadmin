import os
import tempfile
import unittest
from unittest import mock

import pre_commit_macadmin_hooks.check_munkiadmin_scripts as target


class TestCheckMunkiadminScripts(unittest.TestCase):
    def setUp(self):
        # Patch validate_shebangs for all tests
        patcher = mock.patch(
            "pre_commit_macadmin_hooks.check_munkiadmin_scripts.validate_shebangs",
            return_value=True,
        )
        self.mock_validate_shebangs = patcher.start()
        self.addCleanup(patcher.stop)

    def make_temp_script(self, name, content="#!/bin/bash\necho hi\n"):
        tmp = tempfile.NamedTemporaryFile("w+", delete=False)
        tmp.write(content)
        tmp.flush()
        tmp.close()
        # Rename to desired name
        dirname = os.path.dirname(tmp.name)
        new_path = os.path.join(dirname, name)
        os.rename(tmp.name, new_path)
        return new_path

    def test_valid_script(self):
        script_name = "manifest-custom"
        script_path = self.make_temp_script(script_name)
        os.chmod(script_path, 0o755)
        try:
            ret = target.main([script_path])
            self.assertEqual(ret, 0)
        finally:
            os.unlink(script_path)

    def test_invalid_prefix(self):
        script_name = "badprefix-script"
        script_path = self.make_temp_script(script_name)
        os.chmod(script_path, 0o755)
        try:
            with mock.patch("builtins.print") as mock_print:
                ret = target.main([script_path])
                self.assertEqual(ret, 1)
                mock_print.assert_any_call(
                    f"{script_path}: does not start with a valid MunkiAdmin script prefix"
                )
        finally:
            os.unlink(script_path)

    def test_not_executable(self):
        script_name = "manifest-custom"
        script_path = self.make_temp_script(script_name)
        os.chmod(script_path, 0o644)
        try:
            with mock.patch("builtins.print") as mock_print:
                ret = target.main([script_path])
                self.assertEqual(ret, 1)
                mock_print.assert_any_call(f"{script_path}: not executable")
        finally:
            os.unlink(script_path)

    def test_invalid_shebang(self):
        script_name = "manifest-custom"
        script_path = self.make_temp_script(script_name)
        os.chmod(script_path, 0o755)
        self.mock_validate_shebangs.return_value = False
        try:
            with mock.patch("builtins.print") as mock_print:
                ret = target.main([script_path])
                self.assertEqual(ret, 1)
                mock_print.assert_any_call(
                    f"{script_path}: does not start with a valid shebang"
                )
        finally:
            os.unlink(script_path)

    def test_multiple_files(self):
        script1 = self.make_temp_script("manifest-custom")
        script2 = self.make_temp_script("badprefix-script")
        os.chmod(script1, 0o755)
        os.chmod(script2, 0o755)
        try:
            with mock.patch("builtins.print") as mock_print:
                ret = target.main([script1, script2])
                self.assertEqual(ret, 1)
                mock_print.assert_any_call(
                    f"{script2}: does not start with a valid MunkiAdmin script prefix"
                )
        finally:
            os.unlink(script1)
            os.unlink(script2)

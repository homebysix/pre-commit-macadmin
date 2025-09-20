import os
import tempfile
import unittest
from unittest import mock

import pre_commit_macadmin_hooks.check_jamf_scripts as target


class TestCheckJamfScripts(unittest.TestCase):
    def setUp(self):
        # Patch validate_shebangs for controlled behavior
        patcher = mock.patch(
            "pre_commit_hooks.check_jamf_scripts.validate_shebangs", return_value=True
        )
        self.mock_validate = patcher.start()
        self.addCleanup(patcher.stop)

    def create_temp_script(self, content):
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as f:
            f.write(content)
            return f.name

    def test_script_with_valid_shebang(self):
        script = "#!/bin/bash\necho hello world\n"
        path = self.create_temp_script(script)
        try:
            ret = target.main([path])
            self.assertEqual(ret, 0)
        finally:
            os.remove(path)

    def test_script_missing_shebang(self):
        script = "echo hello world\n"
        path = self.create_temp_script(script)
        try:
            ret = target.main([path])
            self.assertEqual(ret, 1)
        finally:
            os.remove(path)

    def test_script_with_env_shebang(self):
        script = "#!/usr/bin/env python3\nprint('hello world')\n"
        path = self.create_temp_script(script)
        try:
            ret = target.main([path])
            self.assertEqual(ret, 1)
        finally:
            os.remove(path)

    def test_script_invalid_shebang(self):
        # Patch validate_shebangs to return False
        self.mock_validate.return_value = False
        script = "#!/bin/bash\necho hello world\n"
        path = self.create_temp_script(script)
        try:
            ret = target.main([path])
            self.assertEqual(ret, 1)
        finally:
            os.remove(path)

    def test_multiple_files(self):
        script1 = "#!/bin/bash\necho hello world\n"
        script2 = "echo hello world\n"
        path1 = self.create_temp_script(script1)
        path2 = self.create_temp_script(script2)
        try:
            ret = target.main([path1, path2])
            self.assertEqual(ret, 1)
        finally:
            os.remove(path1)
            os.remove(path2)

    def test_valid_shebangs_argument(self):
        pass


if __name__ == "__main__":
    unittest.main()

import os
import stat
import tempfile
import unittest
from unittest import mock

import pre_commit_macadmin_hooks.check_outset_scripts as target


class TestCheckOutsetScripts(unittest.TestCase):

    def test_build_argument_parser(self):
        parser = target.build_argument_parser()
        args = parser.parse_args(["file1", "file2"])
        self.assertEqual(args.filenames, ["file1", "file2"])

    @mock.patch(
        "pre_commit_macadmin_hooks.check_outset_scripts.validate_shebangs",
        return_value=True,
    )
    def test_main_executable_and_valid_shebang(self, mock_validate):
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            tf.write(b"#!/bin/bash\necho test\n")
            tf.flush()
            os.chmod(tf.name, os.stat(tf.name).st_mode | stat.S_IXUSR)
            filename = tf.name

        try:
            with mock.patch("builtins.print") as mock_print:
                retval = target.main([filename])
            self.assertEqual(retval, 0)
            mock_print.assert_not_called()
        finally:
            os.unlink(filename)

    @mock.patch(
        "pre_commit_macadmin_hooks.check_outset_scripts.validate_shebangs",
        return_value=False,
    )
    def test_main_invalid_shebang(self, mock_validate):
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            tf.write(b"echo test\n")
            tf.flush()
            os.chmod(tf.name, os.stat(tf.name).st_mode | stat.S_IXUSR)
            filename = tf.name

        try:
            with mock.patch("builtins.print") as mock_print:
                retval = target.main([filename])
            self.assertEqual(retval, 1)
            mock_print.assert_any_call(
                f"{filename}: does not start with a valid shebang"
            )
        finally:
            os.unlink(filename)

    @mock.patch(
        "pre_commit_macadmin_hooks.check_outset_scripts.validate_shebangs",
        return_value=True,
    )
    def test_main_not_executable(self, mock_validate):
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            tf.write(b"#!/bin/bash\necho test\n")
            tf.flush()
            # Remove executable bit
            os.chmod(tf.name, stat.S_IRUSR | stat.S_IWUSR)
            filename = tf.name

        try:
            with mock.patch("builtins.print") as mock_print:
                retval = target.main([filename])
            self.assertEqual(retval, 1)
            mock_print.assert_any_call(f"{filename}: not executable")
        finally:
            os.unlink(filename)

    @mock.patch(
        "pre_commit_macadmin_hooks.check_outset_scripts.validate_shebangs",
        return_value=False,
    )
    def test_main_not_executable_and_invalid_shebang(self, mock_validate):
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            tf.write(b"echo test\n")
            tf.flush()
            os.chmod(tf.name, stat.S_IRUSR | stat.S_IWUSR)
            filename = tf.name

        try:
            with mock.patch("builtins.print") as mock_print:
                retval = target.main([filename])
            self.assertEqual(retval, 1)
            mock_print.assert_any_call(f"{filename}: not executable")
            mock_print.assert_any_call(
                f"{filename}: does not start with a valid shebang"
            )
        finally:
            os.unlink(filename)

    def test_main_no_files(self):
        retval = target.main([])
        self.assertEqual(retval, 0)

import os
import plistlib
import tempfile
import unittest
from unittest import mock

import pre_commit_hooks.check_plists as target


class TestCheckPlists(unittest.TestCase):

    def test_build_argument_parser(self):
        parser = target.build_argument_parser()
        args = parser.parse_args(["file1.plist", "file2.plist"])
        self.assertEqual(args.filenames, ["file1.plist", "file2.plist"])

    def test_main_valid_plist(self):
        # Create a valid plist file
        with tempfile.NamedTemporaryFile("wb", delete=False) as tf:
            plistlib.dump({"foo": "bar"}, tf)
            tfname = tf.name
        try:
            result = target.main([tfname])
            self.assertEqual(result, 0)
        finally:
            os.remove(tfname)

    def test_main_invalid_plist(self):
        # Create an invalid plist file
        with tempfile.NamedTemporaryFile("w", delete=False) as tf:
            tf.write("not a plist")
            tfname = tf.name
        try:
            with mock.patch("builtins.print") as mock_print:
                result = target.main([tfname])
                self.assertEqual(result, 1)
                self.assertTrue(
                    any(tfname in str(call) for call in mock_print.call_args_list[0])
                )
        finally:
            os.remove(tfname)

    def test_main_multiple_files(self):
        # One valid and one invalid plist
        with tempfile.NamedTemporaryFile("wb", delete=False) as tf_valid:
            plistlib.dump({"foo": "bar"}, tf_valid)
            valid_name = tf_valid.name
        with tempfile.NamedTemporaryFile("w", delete=False) as tf_invalid:
            tf_invalid.write("not a plist")
            invalid_name = tf_invalid.name
        try:
            with mock.patch("builtins.print") as mock_print:
                result = target.main([valid_name, invalid_name])
                self.assertEqual(result, 1)
                self.assertTrue(
                    any(
                        invalid_name in str(call)
                        for call in mock_print.call_args_list[0]
                    )
                )
        finally:
            os.remove(valid_name)
            os.remove(invalid_name)

    def test_main_no_files(self):
        result = target.main([])
        self.assertEqual(result, 0)

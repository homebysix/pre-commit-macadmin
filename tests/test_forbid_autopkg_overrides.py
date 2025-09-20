import os
import plistlib
import tempfile
import unittest
from unittest import mock

import pre_commit_macadmin_hooks.forbid_autopkg_overrides as target


class TestForbidAutoPkgOverrides(unittest.TestCase):

    def test_build_argument_parser_no_args(self):
        parser = target.build_argument_parser()
        args = parser.parse_args([])
        self.assertEqual(args.filenames, [])

    def test_build_argument_parser_with_multiple_filenames(self):
        parser = target.build_argument_parser()
        args = parser.parse_args(["foo.plist", "bar.plist"])
        self.assertEqual(args.filenames, ["foo.plist", "bar.plist"])

    def test_build_argument_parser_help_message(self):
        parser = target.build_argument_parser()
        help_text = parser.format_help()
        self.assertIn("Filenames to check.", help_text)
        self.assertIn("usage:", help_text)

    @mock.patch("pre_commit_hooks.forbid_autopkg_overrides.load_autopkg_recipe")
    def test_main_recipe_missing_required_key(self, mock_load):
        # Simulate a recipe missing the "Process" key
        mock_load.return_value = {"Input": "value"}
        with tempfile.NamedTemporaryFile("w", delete=False) as tf:
            filename = tf.name
        try:
            result = target.main([filename])
            self.assertEqual(result, 1)
        finally:
            os.unlink(filename)

    @mock.patch("pre_commit_hooks.forbid_autopkg_overrides.load_autopkg_recipe")
    def test_main_recipe_with_required_key(self, mock_load):
        # Simulate a recipe with the "Process" key
        mock_load.return_value = {"Process": [], "Input": "value"}
        with tempfile.NamedTemporaryFile("w", delete=False) as tf:
            filename = tf.name
        try:
            result = target.main([filename])
            self.assertEqual(result, 0)
        finally:
            os.unlink(filename)

    @mock.patch("pre_commit_hooks.forbid_autopkg_overrides.load_autopkg_recipe")
    def test_main_recipe_load_returns_none(self, mock_load):
        # Simulate load_autopkg_recipe returning None (invalid file)
        mock_load.return_value = None
        with tempfile.NamedTemporaryFile("w", delete=False) as tf:
            filename = tf.name
        try:
            result = target.main([filename])
            self.assertEqual(result, 1)
        finally:
            os.unlink(filename)

    def test_build_argument_parser(self):
        parser = target.build_argument_parser()
        args = parser.parse_args(["file1", "file2"])
        self.assertEqual(args.filenames, ["file1", "file2"])

    @mock.patch("pre_commit_hooks.forbid_autopkg_overrides.load_autopkg_recipe")
    def test_main_multiple_files(self, mock_load):
        # First file is valid, second is missing required key
        mock_load.side_effect = [{"Process": []}, {"Input": "value"}]
        with tempfile.NamedTemporaryFile(
            "w", delete=False
        ) as tf1, tempfile.NamedTemporaryFile("w", delete=False) as tf2:
            filenames = [tf1.name, tf2.name]
        try:
            result = target.main(filenames)
            self.assertEqual(result, 1)
        finally:
            os.unlink(filenames[0])
            os.unlink(filenames[1])

    @mock.patch("pre_commit_hooks.forbid_autopkg_overrides.load_autopkg_recipe")
    def test_main_no_filenames(self, mock_load):
        # No files to check, should return 0
        result = target.main([])
        self.assertEqual(result, 0)

    def test_load_autopkg_recipe_valid(self):
        # Test loading a valid plist file
        data = {"Process": [], "Input": "value"}
        with tempfile.NamedTemporaryFile("wb", delete=False) as tf:
            plistlib.dump(data, tf)
            filename = tf.name
        try:
            result = target.load_autopkg_recipe(filename)
            self.assertEqual(result, data)
        finally:
            os.unlink(filename)

    def test_load_autopkg_recipe_invalid(self):
        # Test loading an invalid plist file
        with tempfile.NamedTemporaryFile("w", delete=False) as tf:
            tf.write("not a plist")
            filename = tf.name
        try:
            result = target.load_autopkg_recipe(filename)
            self.assertIsNone(result)
        finally:
            os.unlink(filename)

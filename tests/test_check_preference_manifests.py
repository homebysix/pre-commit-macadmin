import argparse
import os
import plistlib
import tempfile
import unittest
from unittest import mock

import pre_commit_hooks.check_preference_manifests as target


class TestCheckPreferenceManifests(unittest.TestCase):
    def test_build_argument_parser_returns_parser(self):
        parser = target.build_argument_parser()
        self.assertIsInstance(parser, argparse.ArgumentParser)

    def test_build_argument_parser_parses_filenames(self):
        parser = target.build_argument_parser()
        args = parser.parse_args(["file1", "file2"])
        self.assertEqual(args.filenames, ["file1", "file2"])

    def test_build_argument_parser_parses_no_filenames(self):
        parser = target.build_argument_parser()
        args = parser.parse_args([])
        self.assertEqual(args.filenames, [])

    def test_validate_required_keys_all_present(self):
        d = {"a": 1, "b": 2}
        self.assertTrue(target.validate_required_keys(d, ["a", "b"], "dict", "file"))

    def test_validate_required_keys_missing(self):
        d = {"a": 1}
        with mock.patch("builtins.print") as mprint:
            self.assertFalse(
                target.validate_required_keys(d, ["a", "b"], "dict", "file")
            )
            mprint.assert_called_with("file: dict missing required key b")

    def test_validate_manifest_key_types_valid(self):
        manifest = {
            "pfm_conditionals": [],
            "pfm_description": "desc",
            "pfm_domain": "domain",
            "pfm_format_version": 1,
            "pfm_enabled": True,
            "pfm_last_modified": target.datetime.now(),
        }
        self.assertTrue(target.validate_manifest_key_types(manifest, "file"))

    def test_validate_manifest_key_types_invalid(self):
        manifest = {
            "pfm_description": 123,
        }
        with mock.patch("builtins.print") as mprint:
            self.assertFalse(target.validate_manifest_key_types(manifest, "file"))
            mprint.assert_called()

    def test_validate_list_item_types_valid(self):
        manifest = {
            "pfm_allowed_file_types": ["txt"],
            "pfm_conditionals": [{}],
        }
        self.assertTrue(target.validate_list_item_types(manifest, "file"))

    def test_validate_list_item_types_invalid(self):
        manifest = {
            "pfm_allowed_file_types": [123],
        }
        with mock.patch("builtins.print") as mprint:
            self.assertFalse(target.validate_list_item_types(manifest, "file"))
            mprint.assert_called()

    def test_validate_list_item_types_empty(self):
        manifest = {
            "pfm_allowed_file_types": [],
        }
        self.assertTrue(target.validate_list_item_types(manifest, "file"))

    def test_validate_required_subkeys_all_present(self):
        subkey = {"pfm_subkeys": [{"pfm_name": "foo", "pfm_type": "string"}]}
        self.assertTrue(
            target.validate_required_subkeys(subkey, ["pfm_type", "pfm_name"], "file")
        )

    def test_validate_required_subkeys_missing(self):
        subkey = {"pfm_subkeys": [{"pfm_type": "string"}]}
        with mock.patch("builtins.print") as mprint:
            self.assertFalse(
                target.validate_required_subkeys(
                    subkey, ["pfm_type", "pfm_name"], "file"
                )
            )
            mprint.assert_called()

    def test_validate_pfm_type_strings_valid(self):
        subkey = {"pfm_type": "string"}
        self.assertTrue(target.validate_pfm_type_strings(subkey, "file"))

    def test_validate_pfm_type_strings_deprecated(self):
        subkey = {"pfm_type": "union policy"}
        with mock.patch("builtins.print") as mprint:
            self.assertTrue(target.validate_pfm_type_strings(subkey, "file"))
            mprint.assert_called()

    def test_validate_pfm_type_strings_unexpected(self):
        subkey = {"pfm_type": "notatype"}
        with mock.patch("builtins.print") as mprint:
            self.assertFalse(target.validate_pfm_type_strings(subkey, "file"))
            mprint.assert_called()

    def test_validate_subkey_known_types_valid(self):
        subkey = {"pfm_name": "PayloadIdentifier", "pfm_type": "string"}
        self.assertTrue(target.validate_subkey_known_types(subkey, "file"))

    def test_validate_subkey_known_types_invalid(self):
        subkey = {"pfm_name": "PayloadIdentifier", "pfm_type": "integer"}
        with mock.patch("builtins.print") as mprint:
            self.assertFalse(target.validate_subkey_known_types(subkey, "file"))
            mprint.assert_called()

    def test_validate_pfm_required_valid(self):
        subkey = {"pfm_require": "always"}
        self.assertTrue(target.validate_pfm_required(subkey, "file"))
        subkey = {"pfm_required": True}
        self.assertTrue(target.validate_pfm_required(subkey, "file"))

    def test_validate_pfm_required_invalid(self):
        subkey = {"pfm_require": "sometimes"}
        with mock.patch("builtins.print") as mprint:
            self.assertFalse(target.validate_pfm_required(subkey, "file"))
            mprint.assert_called()
        subkey = {"pfm_required": False}
        with mock.patch("builtins.print") as mprint:
            self.assertFalse(target.validate_pfm_required(subkey, "file"))
            mprint.assert_called()
        subkey = {"pfm_required": True, "pfm_require": "always"}
        with mock.patch("builtins.print") as mprint:
            target.validate_pfm_required(subkey, "file")
            mprint.assert_called()

    def test_validate_pfm_targets_valid(self):
        subkey = {"pfm_targets": ["user", "system"]}
        self.assertTrue(target.validate_pfm_targets(subkey, "file"))

    def test_validate_pfm_targets_invalid(self):
        subkey = {"pfm_targets": ["foo"]}
        with mock.patch("builtins.print") as mprint:
            self.assertFalse(target.validate_pfm_targets(subkey, "file"))
            mprint.assert_called()

    def test_validate_pfm_default_valid(self):
        subkey = {"pfm_type": "string", "pfm_default": "abc"}
        self.assertTrue(target.validate_pfm_default(subkey, "file"))

    def test_validate_pfm_default_invalid(self):
        subkey = {"pfm_type": "string", "pfm_default": 123}
        with mock.patch("builtins.print") as mprint:
            self.assertFalse(target.validate_pfm_default(subkey, "file"))
            mprint.assert_called()

    def test_validate_urls_valid(self):
        subkey = {"pfm_app_url": "http://example.com"}
        self.assertTrue(target.validate_urls(subkey, "file"))

    def test_validate_urls_empty(self):
        subkey = {"pfm_app_url": ""}
        with mock.patch("builtins.print") as mprint:
            self.assertFalse(target.validate_urls(subkey, "file"))
            mprint.assert_called()

    def test_validate_urls_not_url(self):
        subkey = {"pfm_app_url": "not_a_url"}
        with mock.patch("builtins.print") as mprint:
            self.assertFalse(target.validate_urls(subkey, "file"))
            mprint.assert_called()

    def test_validate_platforms_valid(self):
        subkey = {"pfm_platforms": ["macOS", "iOS"]}
        self.assertTrue(target.validate_platforms(subkey, "file"))

    def test_validate_platforms_invalid(self):
        subkey = {"pfm_platforms": ["foo"]}
        with mock.patch("builtins.print") as mprint:
            self.assertFalse(target.validate_platforms(subkey, "file"))
            mprint.assert_called()

    def test_validate_subkeys_all_valid(self):
        subkeys = [
            {
                "pfm_type": "string",
                "pfm_name": "foo",
                "pfm_targets": ["user"],
                "pfm_default": "bar",
            }
        ]
        self.assertTrue(target.validate_subkeys(subkeys, "file"))

    def test_validate_subkeys_invalid(self):
        subkeys = [
            {
                "pfm_type": "notatype",
                "pfm_name": "foo",
            }
        ]
        with mock.patch("builtins.print") as mprint:
            self.assertFalse(target.validate_subkeys(subkeys, "file"))
            mprint.assert_called()

    def test_main_valid_file(self):
        manifest = {
            "pfm_title": "Title",
            "pfm_domain": "com.example",
            "pfm_description": "desc",
            "pfm_format_version": 1,
            "pfm_subkeys": [{"pfm_type": "string", "pfm_name": "foo"}],
        }
        with tempfile.NamedTemporaryFile("wb", delete=False) as tf:
            plistlib.dump(manifest, tf)
            tfname = tf.name
        try:
            self.assertEqual(target.main([tfname]), 0)
        finally:
            os.unlink(tfname)

    def test_main_invalid_plist(self):
        with tempfile.NamedTemporaryFile("wb", delete=False) as tf:
            tf.write(b"notaplist")
            tfname = tf.name
        try:
            with mock.patch("builtins.print") as mprint:
                self.assertEqual(target.main([tfname]), 1)
                mprint.assert_called()
        finally:
            os.unlink(tfname)

    def test_main_missing_required_keys(self):
        manifest = {
            "pfm_title": "Title",
            "pfm_domain": "com.example",
        }
        with tempfile.NamedTemporaryFile("wb", delete=False) as tf:
            plistlib.dump(manifest, tf)
            tfname = tf.name
        try:
            with mock.patch("builtins.print") as mprint:
                self.assertEqual(target.main([tfname]), 1)
                mprint.assert_called()
        finally:
            os.unlink(tfname)

    def test_main_invalid_format_version(self):
        manifest = {
            "pfm_title": "Title",
            "pfm_domain": "com.example",
            "pfm_description": "desc",
            "pfm_format_version": 2,
        }
        with tempfile.NamedTemporaryFile("wb", delete=False) as tf:
            plistlib.dump(manifest, tf)
            tfname = tf.name
        try:
            with mock.patch("builtins.print") as mprint:
                target.main([tfname])
                mprint.assert_called()
        finally:
            os.unlink(tfname)

import json
import os
import plistlib
import tempfile
import unittest
from unittest import mock

import ruamel.yaml

import pre_commit_hooks.check_munkipkg_buildinfo as target


class TestCheckMunkiPkgBuildinfo(unittest.TestCase):
    def test_import(self):
        # Test that the target module imports without error
        self.assertIsNotNone(target)

    def test_build_argument_parser(self):
        parser = target.build_argument_parser()
        args = parser.parse_args(["foo.plist"])
        self.assertEqual(args.filenames, ["foo.plist"])
        self.assertTrue(hasattr(args, "identifier_prefix"))

    def test_validate_buildinfo_key_types_valid(self):
        # All types correct
        buildinfo = {
            "name": "mypkg",
            "version": "1.0",
            "identifier": "com.example.pkg",
            "install_location": "/",
            "distribution_style": True,
            "ownership": "recommended",
            "postinstall_action": "none",
            "preserve_xattr": False,
            "product id": "com.example.product",
            "signing_info": {},
            "suppress_bundle_relocation": False,
        }
        self.assertTrue(target.validate_buildinfo_key_types(buildinfo, "file"))

    def test_validate_buildinfo_key_types_invalid(self):
        # Wrong type for version (should be str)
        buildinfo = {"name": "mypkg", "version": 1}
        with mock.patch("builtins.print") as mock_print:
            self.assertFalse(target.validate_buildinfo_key_types(buildinfo, "file"))
            mock_print.assert_called()

    def test_main_valid_plist(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            plist_path = os.path.join(tmpdir, "test.plist")
            data = {"name": "mypkg", "version": "1.0"}
            with open(plist_path, "wb") as f:
                plistlib.dump(data, f)
            retval = target.main([plist_path])
            self.assertEqual(retval, 0)

    def test_main_invalid_plist(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            plist_path = os.path.join(tmpdir, "bad.plist")
            with open(plist_path, "wb") as f:
                f.write(b"not a plist")
            with mock.patch("builtins.print") as mock_print:
                retval = target.main([plist_path])
                self.assertEqual(retval, 1)
                mock_print.assert_called()

    def test_main_missing_required_keys(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            plist_path = os.path.join(tmpdir, "test.plist")
            data = {"name": "mypkg"}  # missing version
            with open(plist_path, "wb") as f:
                plistlib.dump(data, f)
            with mock.patch("builtins.print") as mock_print:
                retval = target.main([plist_path])
                self.assertEqual(retval, 1)
                mock_print.assert_called()

    def test_main_identifier_prefix(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            plist_path = os.path.join(tmpdir, "test.plist")
            data = {"name": "mypkg", "version": "1.0", "identifier": "com.foo.pkg"}
            with open(plist_path, "wb") as f:
                plistlib.dump(data, f)
            with mock.patch("builtins.print") as mock_print:
                retval = target.main(
                    ["--identifier-prefix", "com.example.", plist_path]
                )
                self.assertEqual(retval, 1)
                mock_print.assert_called()

    def test_main_install_location_warning(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            plist_path = os.path.join(tmpdir, "test.plist")
            data = {"name": "mypkg", "version": "1.0", "install_location": "/notroot"}
            with open(plist_path, "wb") as f:
                plistlib.dump(data, f)
            with mock.patch("builtins.print") as mock_print:
                retval = target.main([plist_path])
                self.assertEqual(retval, 0)
                mock_print.assert_called()

    def test_main_valid_yaml(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_path = os.path.join(tmpdir, "test.yaml")
            data = {"name": "mypkg", "version": "1.0"}
            with open(yaml_path, "w", encoding="utf-8") as f:
                ruamel.yaml.YAML().dump(data, f)
            retval = target.main([yaml_path])
            self.assertEqual(retval, 0)

    def test_main_invalid_yaml(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_path = os.path.join(tmpdir, "bad.yaml")
            with open(yaml_path, "w", encoding="utf-8") as f:
                f.write("not: [valid, yaml")  # malformed YAML
            with mock.patch("builtins.print") as mock_print:
                retval = target.main([yaml_path])
                self.assertEqual(retval, 1)
                mock_print.assert_called()

    def test_main_missing_required_keys_yaml(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_path = os.path.join(tmpdir, "test.yaml")
            data = {"name": "mypkg"}  # missing version
            with open(yaml_path, "w", encoding="utf-8") as f:
                ruamel.yaml.YAML().dump(data, f)
            with mock.patch("builtins.print") as mock_print:
                retval = target.main([yaml_path])
                self.assertEqual(retval, 1)
                mock_print.assert_called()

    def test_main_identifier_prefix_yaml(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_path = os.path.join(tmpdir, "test.yaml")
            data = {"name": "mypkg", "version": "1.0", "identifier": "com.foo.pkg"}
            with open(yaml_path, "w", encoding="utf-8") as f:
                ruamel.yaml.YAML().dump(data, f)
            with mock.patch("builtins.print") as mock_print:
                retval = target.main(["--identifier-prefix", "com.example.", yaml_path])
                self.assertEqual(retval, 1)
                mock_print.assert_called()

    def test_main_install_location_warning_yaml(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_path = os.path.join(tmpdir, "test.yaml")
            data = {"name": "mypkg", "version": "1.0", "install_location": "/notroot"}
            with open(yaml_path, "w", encoding="utf-8") as f:
                ruamel.yaml.YAML().dump(data, f)
            with mock.patch("builtins.print") as mock_print:
                retval = target.main([yaml_path])
                self.assertEqual(retval, 0)
                mock_print.assert_called()

    def test_main_valid_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = os.path.join(tmpdir, "test.json")
            data = {"name": "mypkg", "version": "1.0"}
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data, f)
            retval = target.main([json_path])
            self.assertEqual(retval, 0)

    def test_main_invalid_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = os.path.join(tmpdir, "bad.json")
            with open(json_path, "w", encoding="utf-8") as f:
                f.write("{not: valid, json}")  # malformed JSON
            with mock.patch("builtins.print") as mock_print:
                retval = target.main([json_path])
                self.assertEqual(retval, 1)
                mock_print.assert_called()

    def test_main_missing_required_keys_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = os.path.join(tmpdir, "test.json")
            data = {"name": "mypkg"}  # missing version
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data, f)
            with mock.patch("builtins.print") as mock_print:
                retval = target.main([json_path])
                self.assertEqual(retval, 1)
                mock_print.assert_called()

    def test_main_identifier_prefix_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = os.path.join(tmpdir, "test.json")
            data = {"name": "mypkg", "version": "1.0", "identifier": "com.foo.pkg"}
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data, f)
            with mock.patch("builtins.print") as mock_print:
                retval = target.main(["--identifier-prefix", "com.example.", json_path])
                self.assertEqual(retval, 1)
                mock_print.assert_called()

    def test_main_install_location_warning_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = os.path.join(tmpdir, "test.json")
            data = {"name": "mypkg", "version": "1.0", "install_location": "/notroot"}
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data, f)
            with mock.patch("builtins.print") as mock_print:
                retval = target.main([json_path])
                self.assertEqual(retval, 0)
                mock_print.assert_called()

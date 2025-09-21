"""test_util.py

Unit tests for the shared/utility functions in pre_commit_macadmin_hooks.util module.
"""

import json
import os
import plistlib
import tempfile
import unittest

from pre_commit_macadmin_hooks.util import (
    detect_deprecated_keys,
    detect_typoed_keys,
    load_autopkg_recipe,
    validate_pkginfo_key_types,
    validate_required_keys,
    validate_restart_action_key,
    validate_shebangs,
    validate_supported_architectures,
    validate_uninstall_method,
)

try:
    import ruamel.yaml
except ImportError:
    ruamel = None


class TestUtil(unittest.TestCase):
    def setUp(self):
        self.sample_dict = {"foo": "bar", "baz": 1}

    def test_load_autopkg_recipe_yaml(self):
        if ruamel is None:
            self.skipTest("ruamel.yaml not installed")
        yaml = ruamel.yaml.YAML()
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as tf:
            yaml.dump(self.sample_dict, tf)
            tf.flush()
            tf.close()
            result = load_autopkg_recipe(tf.name)
        os.unlink(tf.name)
        self.assertEqual(result, self.sample_dict)

    def test_load_autopkg_recipe_json(self):
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as tf:
            json.dump(self.sample_dict, tf)
            tf.flush()
            tf.close()
            result = load_autopkg_recipe(tf.name)
        os.unlink(tf.name)
        self.assertEqual(result, self.sample_dict)

    def test_load_autopkg_recipe_plist(self):
        with tempfile.NamedTemporaryFile(suffix=".plist", delete=False) as tf:
            plistlib.dump(self.sample_dict, tf)
            tf.flush()
            tf.close()
            result = load_autopkg_recipe(tf.name)
        os.unlink(tf.name)
        self.assertEqual(result, self.sample_dict)

    def test_load_autopkg_recipe_yaml_parse_error(self):
        if ruamel is None:
            self.skipTest("ruamel.yaml not installed")
        with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w", delete=False) as tf:
            tf.write("not: valid: yaml: :")
            tf.flush()
            tf.close()
            result = load_autopkg_recipe(tf.name)
        os.unlink(tf.name)
        self.assertIsNone(result)

    def test_load_autopkg_recipe_json_parse_error(self):
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as tf:
            tf.write("{not: valid json}")
            tf.flush()
            tf.close()
            result = load_autopkg_recipe(tf.name)
        os.unlink(tf.name)
        self.assertIsNone(result)

    def test_load_autopkg_recipe_plist_parse_error(self):
        with tempfile.NamedTemporaryFile(
            suffix=".plist", mode="wb", delete=False
        ) as tf:
            tf.write(b"not a plist")
            tf.flush()
            tf.close()
            result = load_autopkg_recipe(tf.name)
        os.unlink(tf.name)
        self.assertIsNone(result)

    def test_validate_required_keys(self):
        d = {"foo": 1, "bar": 2}
        self.assertTrue(validate_required_keys(d, "file", ["foo", "bar"]))
        self.assertFalse(validate_required_keys(d, "file", ["foo", "baz"]))

    def test_detect_deprecated_keys(self):
        d = {"forced_install": True}
        self.assertFalse(detect_deprecated_keys(d, "file"))
        d = {"foo": 1}
        self.assertTrue(detect_deprecated_keys(d, "file"))

    def test_detect_typoed_keys(self):
        d = {"blocking_apps": 1}
        self.assertFalse(detect_typoed_keys(d, "file"))
        d = {"condition": "some_condition"}
        self.assertFalse(detect_typoed_keys(d, "file"))
        d = {"foo": 1}
        self.assertTrue(detect_typoed_keys(d, "file"))

    def test_validate_restart_action_key(self):
        d = {"RestartAction": "RequireRestart"}
        self.assertTrue(validate_restart_action_key(d, "file"))
        d = {"RestartAction": "InvalidValue"}
        self.assertFalse(validate_restart_action_key(d, "file"))
        d = {}
        self.assertTrue(validate_restart_action_key(d, "file"))

    def test_validate_uninstall_method(self):
        d = {"uninstall_script": "echo", "uninstall_method": "uninstall_script"}
        self.assertTrue(validate_uninstall_method(d, "file"))
        d = {"uninstall_script": "echo", "uninstall_method": "other"}
        self.assertFalse(validate_uninstall_method(d, "file"))
        d = {"uninstall_method": "uninstall_script"}
        self.assertFalse(validate_uninstall_method(d, "file"))
        d = {}
        self.assertTrue(validate_uninstall_method(d, "file"))

    def test_validate_supported_architectures(self):
        d = {"supported_architectures": ["arm64", "x86_64"]}
        self.assertTrue(validate_supported_architectures(d, "file"))
        d = {"supported_architectures": ["arm64", "foo"]}
        self.assertFalse(validate_supported_architectures(d, "file"))
        d = {}
        self.assertTrue(validate_supported_architectures(d, "file"))

    def test_validate_pkginfo_key_types(self):
        d = {
            "catalogs": ["foo"],
            "blocking_applications": ["bar"],
            "minimum_os_version": "10.15.0",
            "OnDemand": True,
        }
        self.assertTrue(validate_pkginfo_key_types(d, "file"))
        d = {
            "catalogs": "foo",  # should be list
            "blocking_applications": ["bar"],
            "minimum_os_version": "10.15.0",
            "OnDemand": True,
        }
        self.assertFalse(validate_pkginfo_key_types(d, "file"))

    def test_validate_shebangs(self):
        valid_script = "#!/bin/bash\nsomething"
        invalid_script = "#!/usr/bin/env python\nsomething"
        self.assertTrue(validate_shebangs(valid_script, "file"))
        self.assertFalse(validate_shebangs(invalid_script, "file"))
        # Test with additional shebangs
        self.assertTrue(
            validate_shebangs(
                "#!/usr/bin/env python\n", "file", ["#!/usr/bin/env python"]
            )
        )

    def test_validate_required_keys_all_present(self):
        d = {"foo": 1, "bar": 2, "baz": 0}
        # All required keys present and truthy except 'baz' (0 is falsy)
        self.assertFalse(validate_required_keys(d, "file", ["foo", "bar", "baz"]))
        # All required keys present and truthy
        d2 = {"foo": 1, "bar": 2, "baz": 3}
        self.assertTrue(validate_required_keys(d2, "file", ["foo", "bar", "baz"]))

    def test_validate_required_keys_missing(self):
        d = {"foo": 1}
        self.assertFalse(validate_required_keys(d, "file", ["foo", "bar"]))
        self.assertFalse(validate_required_keys(d, "file", ["bar"]))
        self.assertTrue(validate_required_keys(d, "file", []))  # No required keys

    def test_validate_required_keys_falsy_values(self):
        d = {"foo": 0, "bar": "", "baz": None}
        # All present but all falsy, should return False
        self.assertFalse(validate_required_keys(d, "file", ["foo", "bar", "baz"]))
        # Only one required key, present but falsy
        self.assertFalse(validate_required_keys(d, "file", ["foo"]))
        # Only one required key, not present
        self.assertFalse(validate_required_keys({}, "file", ["foo"]))


if __name__ == "__main__":
    unittest.main()

import os
import plistlib
import tempfile
import unittest
from unittest import mock

import pre_commit_hooks.check_munki_pkgsinfo as target


class TestCheckMunkiPkgsinfo(unittest.TestCase):
    def setUp(self):
        # Patch all util functions used in main to always return True unless otherwise specified
        patcher_list = [
            "validate_required_keys",
            "validate_pkginfo_key_types",
            "validate_restart_action_key",
            "validate_uninstall_method",
            "validate_supported_architectures",
            "detect_deprecated_keys",
            "detect_typoed_keys",
            "validate_shebangs",
        ]
        self.patchers = []
        for func in patcher_list:
            p = mock.patch(f"pre_commit_hooks.util.{func}", return_value=True)
            self.patchers.append(p)
            p.start()
        self.addCleanup(lambda: [p.stop() for p in self.patchers])

        # Patch _check_case_sensitive_path to always return True
        self.case_path_patcher = mock.patch.object(
            target, "_check_case_sensitive_path", return_value=True
        )
        self.case_path_patcher.start()
        self.addCleanup(self.case_path_patcher.stop)

        # Patch os.path.isfile to always return True
        self.isfile_patcher = mock.patch("os.path.isfile", return_value=True)
        self.isfile_patcher.start()
        self.addCleanup(self.isfile_patcher.stop)

    def make_pkginfo_file(self, pkginfo_dict):
        tmp = tempfile.NamedTemporaryFile(delete=False)
        plistlib.dump(pkginfo_dict, tmp)
        tmp.close()
        return tmp.name

    def test_valid_pkginfo_returns_zero(self):
        pkginfo = {
            "description": "desc",
            "name": "foo",
            "version": "1.0",
            "category": "Utilities",
            "catalogs": ["testing"],
            "installer_item_location": "foo.pkg",
            "uninstaller_item_location": "foo_un.pkg",
        }
        filename = self.make_pkginfo_file(pkginfo)
        try:
            argv = [
                "--categories",
                "Utilities",
                "--catalogs",
                "testing",
                filename,
            ]
            ret = target.main(argv)
            self.assertEqual(ret, 0)
        finally:
            os.unlink(filename)

    # def test_missing_required_key_returns_one(self):
    #     # Patch validate_required_keys to return False
    #     with mock.patch(
    #         "pre_commit_hooks.util.validate_required_keys", return_value=False
    #     ):
    #         pkginfo = {
    #             "name": "foo",
    #             "version": "1.0",
    #             "category": "Utilities",
    #             "catalogs": ["testing"],
    #             "installer_item_location": "foo.pkg",
    #             "uninstaller_item_location": "foo_un.pkg",
    #         }
    #         filename = self.make_pkginfo_file(pkginfo)
    #         try:
    #             argv = [
    #                 "--categories",
    #                 "Utilities",
    #                 "--catalogs",
    #                 "testing",
    #                 filename,
    #             ]
    #             ret = target.main(argv)
    #             self.assertEqual(ret, 1)
    #         finally:
    #             os.unlink(filename)

    def test_plist_parse_error_returns_one(self):
        with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
            tmp.write("not a plist")
            tmp_filename = tmp.name
        try:
            argv = [tmp_filename]
            ret = target.main(argv)
            self.assertEqual(ret, 1)
        finally:
            os.unlink(tmp_filename)

    def test_deprecated_installer_type_warns(self):
        pkginfo = {
            "description": "desc",
            "name": "foo",
            "version": "1.0",
            "category": "Utilities",
            "catalogs": ["testing"],
            "installer_item_location": "foo.pkg",
            "uninstaller_item_location": "foo_un.pkg",
            "installer_type": "AdobeSetup",
        }
        filename = self.make_pkginfo_file(pkginfo)
        try:
            argv = [filename]
            with mock.patch("builtins.print") as mprint:
                target.main(argv)
                self.assertTrue(
                    any("installer_type" in str(c) for c in mprint.call_args_list)
                )
        finally:
            os.unlink(filename)

    def test_deprecated_uninstall_method_warns(self):
        pkginfo = {
            "description": "desc",
            "name": "foo",
            "version": "1.0",
            "category": "Utilities",
            "catalogs": ["testing"],
            "installer_item_location": "foo.pkg",
            "uninstaller_item_location": "foo_un.pkg",
            "uninstall_method": "AdobeSetup",
        }
        filename = self.make_pkginfo_file(pkginfo)
        try:
            argv = [filename]
            with mock.patch("builtins.print") as mprint:
                target.main(argv)
                self.assertTrue(
                    any("uninstall_method" in str(c) for c in mprint.call_args_list)
                )
        finally:
            os.unlink(filename)

    # def test_rogue_category_returns_one(self):
    #     pkginfo = {
    #         "description": "desc",
    #         "name": "foo",
    #         "version": "1.0",
    #         "category": "BadCategory",
    #         "catalogs": ["testing"],
    #         "installer_item_location": "foo.pkg",
    #         "uninstaller_item_location": "foo_un.pkg",
    #     }
    #     filename = self.make_pkginfo_file(pkginfo)
    #     try:
    #         argv = ["--categories", "Utilities", filename]
    #         ret = target.main(argv)
    #         self.assertEqual(ret, 1)
    #     finally:
    #         os.unlink(filename)

    # def test_rogue_catalog_returns_one(self):
    #     pkginfo = {
    #         "description": "desc",
    #         "name": "foo",
    #         "version": "1.0",
    #         "category": "Utilities",
    #         "catalogs": ["notapproved"],
    #         "installer_item_location": "foo.pkg",
    #         "uninstaller_item_location": "foo_un.pkg",
    #     }
    #     filename = self.make_pkginfo_file(pkginfo)
    #     try:
    #         argv = ["--catalogs", "testing", filename]
    #         ret = target.main(argv)
    #         self.assertEqual(ret, 1)
    #     finally:
    #         os.unlink(filename)

    def test_missing_icon_returns_one(self):
        # Patch os.path.isfile to return False
        with mock.patch("os.path.isfile", return_value=False):
            pkginfo = {
                "description": "desc",
                "name": "foo",
                "version": "1.0",
                "category": "Utilities",
                "catalogs": ["testing"],
                "installer_item_location": "foo.pkg",
                "uninstaller_item_location": "foo_un.pkg",
            }
            filename = self.make_pkginfo_file(pkginfo)
            try:
                argv = [filename]
                ret = target.main(argv)
                self.assertEqual(ret, 1)
            finally:
                os.unlink(filename)

    def test_items_to_copy_trailing_slash_returns_one(self):
        pkginfo = {
            "description": "desc",
            "name": "foo",
            "version": "1.0",
            "category": "Utilities",
            "catalogs": ["testing"],
            "installer_item_location": "foo.pkg",
            "uninstaller_item_location": "foo_un.pkg",
            "items_to_copy": [{"destination_path": "/Applications/"}],
        }
        filename = self.make_pkginfo_file(pkginfo)
        try:
            argv = [filename]
            ret = target.main(argv)
            self.assertEqual(ret, 1)
        finally:
            os.unlink(filename)

    def test_duplicate_import_returns_one(self):
        pkginfo = {
            "description": "desc",
            "name": "foo",
            "version": "1.0",
            "category": "Utilities",
            "catalogs": ["testing"],
            "installer_item_location": "foo__1.pkg",
            "uninstaller_item_location": "foo_un__1.pkg",
        }
        filename = self.make_pkginfo_file(pkginfo)
        try:
            argv = [filename]
            ret = target.main(argv)
            self.assertEqual(ret, 1)
        finally:
            os.unlink(filename)

    def test_require_pkg_blocking_apps_missing_returns_one(self):
        pkginfo = {
            "description": "desc",
            "name": "foo",
            "version": "1.0",
            "category": "Utilities",
            "catalogs": ["testing"],
            "installer_item_location": "foo.pkg",
            "uninstaller_item_location": "foo_un.pkg",
        }
        filename = self.make_pkginfo_file(pkginfo)
        try:
            argv = ["--require-pkg-blocking-apps", filename]
            ret = target.main(argv)
            self.assertEqual(ret, 1)
        finally:
            os.unlink(filename)

    def test_script_with_invalid_shebang_returns_one(self):
        # Patch validate_shebangs to return False
        with mock.patch("pre_commit_hooks.util.validate_shebangs", return_value=False):
            pkginfo = {
                "description": "desc",
                "name": "foo",
                "version": "1.0",
                "category": "Utilities",
                "catalogs": ["testing"],
                "installer_item_location": "foo.pkg",
                "uninstaller_item_location": "foo_un.pkg",
                "postinstall_script": "echo hi",
            }
            filename = self.make_pkginfo_file(pkginfo)
            try:
                argv = [filename]
                ret = target.main(argv)
                self.assertEqual(ret, 1)
            finally:
                os.unlink(filename)

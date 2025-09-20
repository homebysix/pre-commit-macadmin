import os
import tempfile
import unittest
from unittest import mock

import pre_commit_macadmin_hooks.check_jamf_profiles as target


class TestCheckJamfProfiles(unittest.TestCase):
    def setUp(self):
        # Create a valid plist file
        self.valid_plist = tempfile.NamedTemporaryFile(delete=False)
        self.valid_plist.write(
            b"<?xml version='1.0' encoding='UTF-8'?><plist version='1.0'><dict><key>foo</key><string>bar</string></dict></plist>"
        )
        self.valid_plist.close()

        # Create an invalid plist file
        self.invalid_plist = tempfile.NamedTemporaryFile(delete=False)
        self.invalid_plist.write(b"not a plist")
        self.invalid_plist.close()

    def tearDown(self):
        os.unlink(self.valid_plist.name)
        os.unlink(self.invalid_plist.name)

    def test_main_with_valid_plist(self):
        retval = target.main([self.valid_plist.name])
        self.assertEqual(retval, 0)

    def test_main_with_invalid_plist(self):
        with mock.patch("builtins.print") as mock_print:
            retval = target.main([self.invalid_plist.name])
            self.assertEqual(retval, 1)
            mock_print.assert_called()
            self.assertIn("plist parsing error", mock_print.call_args[0][0])

    def test_main_with_multiple_files(self):
        with mock.patch("builtins.print") as mock_print:
            retval = target.main([self.valid_plist.name, self.invalid_plist.name])
            self.assertEqual(retval, 1)
            mock_print.assert_called()
            self.assertIn(self.invalid_plist.name, mock_print.call_args[0][0])

    def test_main_with_no_files(self):
        retval = target.main([])
        self.assertEqual(retval, 0)

    def test_argument_parser(self):
        parser = target.build_argument_parser()
        args = parser.parse_args([self.valid_plist.name])
        self.assertIn(self.valid_plist.name, args.filenames)

import tempfile
import unittest
from unittest import mock

import pre_commit_hooks.munki_makecatalogs as target


class TestMunkiMakecatalogs(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory to act as a fake munki repo
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo_path = self.tempdir.name

    def tearDown(self):
        self.tempdir.cleanup()

    @mock.patch("os.path.isdir")
    @mock.patch("os.path.isfile")
    @mock.patch("subprocess.call")
    def test_main_success(self, mock_call, mock_isfile, mock_isdir):
        mock_isdir.return_value = True
        mock_isfile.return_value = True
        mock_call.return_value = 0

        ret = target.main(["--munki-repo", self.repo_path])
        self.assertEqual(ret, 0)
        mock_call.assert_called_once_with(
            ["/usr/local/munki/makecatalogs", self.repo_path]
        )

    @mock.patch("os.path.isdir")
    def test_main_missing_pkgsinfo(self, mock_isdir):
        mock_isdir.return_value = False
        with mock.patch("builtins.print") as mock_print:
            ret = target.main(["--munki-repo", self.repo_path])
            self.assertEqual(ret, 1)
            mock_print.assert_any_call("Could not find pkgsinfo folder.")

    @mock.patch("os.path.isdir")
    @mock.patch("os.path.isfile")
    def test_main_missing_makecatalogs(self, mock_isfile, mock_isdir):
        mock_isdir.return_value = True
        mock_isfile.return_value = False
        with mock.patch("builtins.print") as mock_print:
            ret = target.main(["--munki-repo", self.repo_path])
            self.assertEqual(ret, 1)
            mock_print.assert_any_call("/usr/local/munki/makecatalogs does not exist.")

    def test_build_argument_parser_defaults(self):
        parser = target.build_argument_parser()
        args = parser.parse_args([])
        self.assertEqual(args.munki_repo, ".")

    def test_build_argument_parser_custom_repo(self):
        parser = target.build_argument_parser()
        args = parser.parse_args(["--munki-repo", "/foo/bar"])
        self.assertEqual(args.munki_repo, "/foo/bar")

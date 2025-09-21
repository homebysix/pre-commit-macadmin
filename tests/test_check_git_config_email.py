import unittest
from unittest import mock

import pre_commit_macadmin_hooks.check_git_config_email as target


class TestCheckGitConfigEmail(unittest.TestCase):
    def setUp(self):
        self.parser = target.build_argument_parser()

    def test_parser_domains_argument(self):
        args = self.parser.parse_args(["--domains", "example.com", "test.com"])
        self.assertEqual(args.domains, ["example.com", "test.com"])

    @mock.patch("subprocess.run")
    def test_email_not_set(self, mock_run):
        mock_run.return_value = mock.Mock(stdout="", returncode=0)
        with mock.patch("builtins.print") as mock_print:
            retval = target.main(["--domains", "example.com"])
            self.assertEqual(retval, 1)
            mock_print.assert_any_call("Git config email is not set.")

    @mock.patch("subprocess.run")
    def test_email_invalid_format(self, mock_run):
        mock_run.return_value = mock.Mock(stdout="notanemail", returncode=0)
        with mock.patch("builtins.print") as mock_print:
            retval = target.main(["--domains", "example.com"])
            self.assertEqual(retval, 1)
            mock_print.assert_any_call(
                "Git config email does not look like an email address."
            )
            mock_print.assert_any_call("Git config email: notanemail")

    @mock.patch("subprocess.run")
    def test_email_unexpected_domain(self, mock_run):
        mock_run.return_value = mock.Mock(stdout="user@other.com", returncode=0)
        with mock.patch("builtins.print") as mock_print:
            retval = target.main(["--domains", "example.com", "test.com"])
            self.assertEqual(retval, 1)
            mock_print.assert_any_call("Git config email is from an unexpected domain.")
            mock_print.assert_any_call("Git config email: user@other.com")
            mock_print.assert_any_call("Expected domains: ['example.com', 'test.com']")

    @mock.patch("subprocess.run")
    def test_email_expected_domain(self, mock_run):
        mock_run.return_value = mock.Mock(stdout="user@example.com", returncode=0)
        retval = target.main(["--domains", "example.com", "test.com"])
        self.assertEqual(retval, 0)

    @mock.patch("subprocess.run")
    def test_no_domains_argument(self, mock_run):
        # Should not check email if no domains are provided
        retval = target.main([])
        self.assertEqual(retval, 0)
        mock_run.assert_not_called()

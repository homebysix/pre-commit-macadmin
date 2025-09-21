import unittest
from unittest import mock

import pre_commit_macadmin_hooks.forbid_autopkg_trust_info as target


class TestForbidAutoPkgTrustInfo(unittest.TestCase):
    def test_build_argument_parser(self):
        parser = target.build_argument_parser()
        args = parser.parse_args(["file1", "file2"])
        self.assertEqual(args.filenames, ["file1", "file2"])

    @mock.patch(
        "pre_commit_macadmin_hooks.forbid_autopkg_trust_info.load_autopkg_recipe"
    )
    def test_main_no_files(self, mock_load):
        # No files provided, should return 0
        ret = target.main([])
        self.assertEqual(ret, 0)
        mock_load.assert_not_called()

    @mock.patch(
        "pre_commit_macadmin_hooks.forbid_autopkg_trust_info.load_autopkg_recipe"
    )
    def test_main_file_with_no_recipe(self, mock_load):
        mock_load.return_value = None
        ret = target.main(["fakefile"])
        self.assertEqual(ret, 1)
        mock_load.assert_called_once_with("fakefile")

    @mock.patch(
        "pre_commit_macadmin_hooks.forbid_autopkg_trust_info.load_autopkg_recipe"
    )
    def test_main_file_with_trust_info(self, mock_load):
        mock_load.return_value = {"ParentRecipeTrustInfo": {}}
        with mock.patch("builtins.print") as mock_print:
            ret = target.main(["recipe_with_trust"])
            self.assertEqual(ret, 1)
            mock_print.assert_called_once_with(
                "recipe_with_trust: trust info in recipe"
            )

    @mock.patch(
        "pre_commit_macadmin_hooks.forbid_autopkg_trust_info.load_autopkg_recipe"
    )
    def test_main_file_without_trust_info(self, mock_load):
        mock_load.return_value = {"Input": {}}
        ret = target.main(["recipe_without_trust"])
        self.assertEqual(ret, 0)

    @mock.patch(
        "pre_commit_macadmin_hooks.forbid_autopkg_trust_info.load_autopkg_recipe"
    )
    def test_main_multiple_files(self, mock_load):
        # First file: valid, second: missing, third: has trust info
        mock_load.side_effect = [{"Input": {}}, None, {"ParentRecipeTrustInfo": {}}]
        with mock.patch("builtins.print") as mock_print:
            ret = target.main(["good", "missing", "bad"])
            self.assertEqual(ret, 1)
            mock_print.assert_called_once_with("bad: trust info in recipe")
        self.assertEqual(mock_load.call_count, 3)

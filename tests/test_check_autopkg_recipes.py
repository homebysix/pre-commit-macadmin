import io
import os
import tempfile
import unittest
from unittest import mock

import pre_commit_hooks.check_autopkg_recipes as target


class TestCheckAutopkgRecipes(unittest.TestCase):

    def test_build_argument_parser_returns_parser(self):
        parser = target.build_argument_parser()
        args = parser.parse_args(["foo.download.recipe", "foo.munki.recipe.yaml"])
        self.assertEqual(
            args.filenames, ["foo.download.recipe", "foo.munki.recipe.yaml"]
        )

    def test_validate_recipe_prefix_passes_with_valid_prefix(self):
        recipe = {"Identifier": "local.test.recipe"}
        self.assertTrue(
            target.validate_recipe_prefix(recipe, "file.recipe", ["local."])
        )

    def test_validate_recipe_prefix_fails_with_invalid_prefix(self):
        recipe = {"Identifier": "foo.test.recipe"}
        with mock.patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            result = target.validate_recipe_prefix(recipe, "file.recipe", ["local."])
            out = mock_stdout.getvalue()
        self.assertFalse(result)
        self.assertIn("file.recipe: identifier does not start with local.", out)

    def test_validate_recipe_prefix_multiple_prefixes(self):
        recipe = {"Identifier": "foo.test.recipe"}
        with mock.patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            result = target.validate_recipe_prefix(
                recipe, "file.recipe", ["local.", "bar."]
            )
            out = mock_stdout.getvalue()
        self.assertFalse(result)
        self.assertIn('one of: "local.", "bar."', out)

    def test_validate_comments_warns_on_html_comment_non_strict(self):
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".recipe") as tf:
            tf.write('{"Identifier": "local.test.recipe"} <!-- comment -->')
            tf.flush()
            tf_name = tf.name
        try:
            with mock.patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
                result = target.validate_comments(tf_name, strict=False)
                out = mock_stdout.getvalue()
            self.assertTrue(result)
            self.assertIn(
                "WARNING: Recommend converting from <!-- --> style comments", out
            )
        finally:
            os.unlink(tf_name)

    def test_validate_comments_fails_on_html_comment_strict(self):
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".recipe") as tf:
            tf.write('{"Identifier": "local.test.recipe"} <!-- comment -->')
            tf.flush()
            tf_name = tf.name
        try:
            with mock.patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
                result = target.validate_comments(tf_name, strict=True)
                out = mock_stdout.getvalue()
            self.assertFalse(result)
            self.assertIn("Convert from <!-- --> style comments to a Comment key", out)
        finally:
            os.unlink(tf_name)

    def test_validate_comments_passes_without_html_comment(self):
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".recipe") as tf:
            tf.write('{"Identifier": "local.test.recipe"}')
            tf.flush()
            tf_name = tf.name
        try:
            result = target.validate_comments(tf_name, strict=True)
            self.assertTrue(result)
        finally:
            os.unlink(tf_name)

    def test_validate_processor_keys_passes(self):
        process = [{"Processor": "TestProc"}, {"Processor": "AnotherProc"}]
        self.assertTrue(target.validate_processor_keys(process, "file.recipe"))

    def test_validate_processor_keys_fails(self):
        process = [{"Processor": "TestProc"}, {"Arg": "val"}]
        with mock.patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            result = target.validate_processor_keys(process, "file.recipe")
            out = mock_stdout.getvalue()
        self.assertFalse(result)
        self.assertIn('missing "Processor" key', out)

    def test_validate_endofcheckphase_passes_no_downloader(self):
        process = [{"Processor": "OtherProc"}]
        self.assertTrue(target.validate_endofcheckphase(process, "file.recipe"))

    def test_validate_endofcheckphase_fails_missing_endofcheck(self):
        process = [{"Processor": "URLDownloader"}]
        with mock.patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            result = target.validate_endofcheckphase(process, "file.recipe")
            out = mock_stdout.getvalue()
        self.assertFalse(result)
        self.assertIn(
            "Contains a download processor, but no EndOfCheckPhase processor", out
        )

    def test_validate_endofcheckphase_fails_wrong_order(self):
        process = [
            {"Processor": "EndOfCheckPhase"},
            {"Processor": "URLDownloader"},
        ]
        with mock.patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            result = target.validate_endofcheckphase(process, "file.recipe")
            out = mock_stdout.getvalue()
        self.assertFalse(result)
        self.assertIn("EndOfCheckPhase typically goes after a download processor", out)

    def test_validate_minimumversion_non_string(self):
        process = [{"Processor": "AppPkgCreator"}]
        with mock.patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            result = target.validate_minimumversion(process, 1.0, "1.0", "file.recipe")
            out = mock_stdout.getvalue()
        self.assertFalse(result)
        self.assertIn("MinimumVersion should be a string", out)

    def test_validate_minimumversion_too_low(self):
        process = [{"Processor": "AppPkgCreator"}]
        with mock.patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            result = target.validate_minimumversion(
                process, "0.5", "1.0", "file.recipe"
            )
            out = mock_stdout.getvalue()
        self.assertFalse(result)
        self.assertIn("AppPkgCreator processor requires minimum AutoPkg version", out)

    def test_validate_minimumversion_passes(self):
        process = [{"Processor": "AppPkgCreator"}]
        result = target.validate_minimumversion(process, "1.0", "1.0", "file.recipe")
        self.assertTrue(result)

    def test_validate_no_deprecated_procs_warns(self):
        process = [{"Processor": "CURLDownloader"}]
        with mock.patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            result = target.validate_no_deprecated_procs(process, "file.recipe")
            out = mock_stdout.getvalue()
        self.assertTrue(result)
        self.assertIn("WARNING: Deprecated processor CURLDownloader is used", out)

    def test_validate_no_superclass_procs_warns(self):
        process = [{"Processor": "URLGetter"}]
        with mock.patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            result = target.validate_no_superclass_procs(process, "file.recipe")
            out = mock_stdout.getvalue()
        self.assertTrue(result)
        self.assertIn("intended to be used by other processors", out)

    def test_validate_jamf_processor_order_warns(self):
        process = [
            {
                "Processor": "com.github.grahampugh.jamf-upload.processors/JamfPolicyUploader"
            },
            {
                "Processor": "com.github.grahampugh.jamf-upload.processors/JamfCategoryUploader"
            },
        ]
        with mock.patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            result = target.validate_jamf_processor_order(process, "file.recipe")
            out = mock_stdout.getvalue()
        self.assertTrue(result)
        self.assertIn("JamfUploader processors are not in the recommended order", out)

    def test_validate_no_var_in_app_path_fails(self):
        process = [
            {
                "Processor": "CodeSignatureVerifier",
                "Arguments": {"input_path": "/Applications/%NAME%.app"},
            }
        ]
        with mock.patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            result = target.validate_no_var_in_app_path(process, "file.recipe")
            out = mock_stdout.getvalue()
        self.assertFalse(result)
        self.assertIn("Use actual app name instead of %NAME%.app", out)

    def test_validate_no_var_in_app_path_passes(self):
        process = [
            {
                "Processor": "CodeSignatureVerifier",
                "Arguments": {"input_path": "/Applications/RealApp.app"},
            }
        ]
        result = target.validate_no_var_in_app_path(process, "file.recipe")
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()

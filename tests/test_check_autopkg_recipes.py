import os
import tempfile
import unittest
from unittest import mock

import pre_commit_macadmin_hooks.check_autopkg_recipes as target


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
        with mock.patch("builtins.print") as mock_print:
            result = target.validate_recipe_prefix(recipe, "file.recipe", ["local."])
        self.assertFalse(result)
        mock_print.assert_called_with(
            "file.recipe: identifier does not start with local."
        )

    def test_validate_recipe_prefix_multiple_prefixes(self):
        recipe = {"Identifier": "foo.test.recipe"}
        with mock.patch("builtins.print") as mock_print:
            result = target.validate_recipe_prefix(
                recipe, "file.recipe", ["local.", "bar."]
            )
        self.assertFalse(result)
        mock_print.assert_called_with(
            'file.recipe: identifier does not start with one of: "local.", "bar."'
        )

    def test_validate_comments_warns_on_html_comment_non_strict(self):
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".recipe") as tf:
            tf.write('{"Identifier": "local.test.recipe"} <!-- comment -->')
            tf.flush()
            tf_name = tf.name
        try:
            with mock.patch("builtins.print") as mock_print:
                result = target.validate_comments(tf_name, strict=False)
            self.assertTrue(result)
            mock_print.assert_called_with(
                f"{tf_name}: WARNING: Recommend converting from <!-- --> style comments to a Comment key."
            )
        finally:
            os.unlink(tf_name)

    def test_validate_comments_fails_on_html_comment_strict(self):
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".recipe") as tf:
            tf.write('{"Identifier": "local.test.recipe"} <!-- comment -->')
            tf.flush()
            tf_name = tf.name
        try:
            with mock.patch("builtins.print") as mock_print:
                result = target.validate_comments(tf_name, strict=True)
            self.assertFalse(result)
            mock_print.assert_called_with(
                f"{tf_name}: Convert from <!-- --> style comments to a Comment key."
            )
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
        with mock.patch("builtins.print") as mock_print:
            result = target.validate_processor_keys(process, "file.recipe")
        self.assertFalse(result)
        mock_print.assert_called_with(
            "file.recipe: Item in processor array is missing \"Processor\" key:\n{'Arg': 'val'}"
        )

    def test_validate_endofcheckphase_passes_no_downloader(self):
        process = [{"Processor": "OtherProc"}]
        self.assertTrue(target.validate_endofcheckphase(process, "file.recipe"))

    def test_validate_endofcheckphase_fails_missing_endofcheck(self):
        process = [{"Processor": "URLDownloader"}]
        with mock.patch("builtins.print") as mock_print:
            result = target.validate_endofcheckphase(process, "file.recipe")
        self.assertFalse(result)
        mock_print.assert_called_with(
            "file.recipe: Contains a download processor, but no EndOfCheckPhase processor."
        )

    def test_validate_endofcheckphase_fails_wrong_order(self):
        process = [
            {"Processor": "EndOfCheckPhase"},
            {"Processor": "URLDownloader"},
        ]
        with mock.patch("builtins.print") as mock_print:
            result = target.validate_endofcheckphase(process, "file.recipe")
        self.assertFalse(result)
        mock_print.assert_called_with(
            "file.recipe: EndOfCheckPhase typically goes after a download processor, not before."
        )

    def test_validate_minimumversion_non_string(self):
        process = [{"Processor": "AppPkgCreator"}]
        with mock.patch("builtins.print") as mock_print:
            result = target.validate_minimumversion(process, 1.0, "1.0", "file.recipe")
        self.assertFalse(result)
        mock_print.assert_called_with("file.recipe: MinimumVersion should be a string.")

    def test_validate_minimumversion_invalid_string(self):
        process = [{"Processor": "AppPkgCreator"}]
        with mock.patch("builtins.print") as mock_print:
            result = target.validate_minimumversion(
                process, "not-a-version", "1.0", "file.recipe"
            )
        self.assertFalse(result)
        mock_print.assert_called_with(
            "file.recipe: MinimumVersion 'not-a-version' is not a valid version string."
        )

    def test_validate_minimumversion_too_low(self):
        process = [{"Processor": "AppPkgCreator"}]
        with mock.patch("builtins.print") as mock_print:
            result = target.validate_minimumversion(
                process, "0.5", "1.0", "file.recipe"
            )
        self.assertFalse(result)
        mock_print.assert_called_with(
            "file.recipe: AppPkgCreator processor requires minimum AutoPkg version 1.0"
        )

    def test_validate_minimumversion_passes(self):
        process = [{"Processor": "AppPkgCreator"}]
        result = target.validate_minimumversion(process, "1.0", "1.0", "file.recipe")
        self.assertTrue(result)

    def test_validate_minimumversion_checks_processor_arguments(self):
        process = [
            {
                "Processor": "SparkleUpdateInfoProvider",
                "Arguments": {"urlencode_path_component": True},
            }
        ]
        with mock.patch("builtins.print") as mock_print:
            result = target.validate_minimumversion(
                process, "1.0", "1.0", "file.recipe"
            )
        self.assertFalse(result)
        mock_print.assert_called_with(
            "file.recipe: SparkleUpdateInfoProvider urlencode_path_component argument "
            "requires minimum AutoPkg version 1.1"
        )

    def test_validate_minimumversion_unknown_argument_falls_back_to_processor(self):
        process = [
            {
                "Processor": "AppPkgCreator",
                "Arguments": {"unknown_future_argument": True},
            }
        ]
        with mock.patch("builtins.print") as mock_print:
            result = target.validate_minimumversion(
                process, "0.9", "1.0", "file.recipe"
            )
        self.assertFalse(result)
        mock_print.assert_called_with(
            "file.recipe: AppPkgCreator processor requires minimum AutoPkg version 1.0"
        )

    def test_validate_minimumversion_unknown_processor_is_skipped(self):
        process = [
            {
                "Processor": "com.github.example.processors/CustomProcessor",
                "Arguments": {"urlencode_path_component": True},
            }
        ]
        result = target.validate_minimumversion(
            process, "0.1.0", "0.1.0", "file.recipe"
        )
        self.assertTrue(result)

    def test_validate_minimumversion_ignore_floor_suppresses_argument_requirement(self):
        process = [
            {
                "Processor": "SparkleUpdateInfoProvider",
                "Arguments": {"urlencode_path_component": True},
            }
        ]
        result = target.validate_minimumversion(process, "1.0", "2.0", "file.recipe")
        self.assertTrue(result)

    def test_validate_no_deprecated_procs_fails_removed_processor(self):
        process = [{"Processor": "RemovedProcessor"}]
        proc_versions = {
            "RemovedProcessor": {
                "_introduced_": "1.0.0",
                "_removed_": "3.0.0",
            }
        }
        with mock.patch.object(target, "PROC_VERSIONS", proc_versions):
            with mock.patch("builtins.print") as mock_print:
                result = target.validate_no_deprecated_procs(process, "file.recipe")
        self.assertFalse(result)
        mock_print.assert_called_with(
            "file.recipe: Processor RemovedProcessor was removed in AutoPkg 3.0.0."
        )

    def test_validate_no_deprecated_procs_skips_unknown_processor(self):
        process = [{"Processor": "com.github.example.processors/CustomProcessor"}]
        with mock.patch.object(target, "PROC_VERSIONS", {}):
            result = target.validate_no_deprecated_procs(process, "file.recipe")
        self.assertTrue(result)

    def test_validate_no_deprecated_procs_warns_deprecated_processor(self):
        process = [{"Processor": "DeprecatedProcessor"}]
        proc_versions = {
            "DeprecatedProcessor": {
                "_introduced_": "1.0.0",
                "_deprecated_": "2.0.0",
            }
        }
        with mock.patch.object(target, "PROC_VERSIONS", proc_versions):
            with mock.patch("builtins.print") as mock_print:
                result = target.validate_no_deprecated_procs(process, "file.recipe")
        self.assertTrue(result)
        mock_print.assert_called_with(
            "file.recipe: WARNING: Processor DeprecatedProcessor was deprecated in AutoPkg 2.0.0."
        )

    def test_validate_no_deprecated_procs_removed_wins_over_deprecated(self):
        process = [{"Processor": "RemovedProcessor"}]
        proc_versions = {
            "RemovedProcessor": {
                "_introduced_": "1.0.0",
                "_deprecated_": "2.0.0",
                "_removed_": "3.0.0",
            }
        }
        with mock.patch.object(target, "PROC_VERSIONS", proc_versions):
            with mock.patch("builtins.print") as mock_print:
                result = target.validate_no_deprecated_procs(process, "file.recipe")
        self.assertFalse(result)
        mock_print.assert_called_once_with(
            "file.recipe: Processor RemovedProcessor was removed in AutoPkg 3.0.0."
        )

    def test_validate_no_superclass_procs_warns(self):
        process = [{"Processor": "URLGetter"}]
        with mock.patch("builtins.print") as mock_print:
            result = target.validate_no_superclass_procs(process, "file.recipe")
        self.assertTrue(result)
        mock_print.assert_called_with(
            "file.recipe: WARNING: The processor URLGetter is intended to be used by other processors, not used directly in recipes."
        )

    def test_validate_jamf_processor_order_warns(self):
        process = [
            {
                "Processor": "com.github.grahampugh.jamf-upload.processors/JamfPolicyUploader"
            },
            {
                "Processor": "com.github.grahampugh.jamf-upload.processors/JamfCategoryUploader"
            },
        ]
        with mock.patch("builtins.print") as mock_print:
            result = target.validate_jamf_processor_order(process, "file.recipe")
        self.assertTrue(result)
        mock_print.assert_called_with(
            "file.recipe: WARNING: JamfUploader processors are not in the recommended order: JamfCategoryUploader, JamfPolicyUploader."
        )

    def test_validate_no_var_in_app_path_fails(self):
        process = [
            {
                "Processor": "CodeSignatureVerifier",
                "Arguments": {"input_path": "/Applications/%NAME%.app"},
            }
        ]
        with mock.patch("builtins.print") as mock_print:
            result = target.validate_no_var_in_app_path(process, "file.recipe")
        self.assertFalse(result)
        mock_print.assert_called_with(
            "file.recipe: Use actual app name instead of %NAME%.app in CodeSignatureVerifier processor argument."
        )

    def test_validate_no_var_in_app_path_passes(self):
        process = [
            {
                "Processor": "CodeSignatureVerifier",
                "Arguments": {"input_path": "/Applications/RealApp.app"},
            }
        ]
        result = target.validate_no_var_in_app_path(process, "file.recipe")
        self.assertTrue(result)

    def test_validate_proc_type_conventions_unknown_type_passes(self):
        # Unknown recipe type should skip validation and pass with warning
        process = [{"Processor": "MunkiImporter"}]
        with mock.patch("builtins.print") as mock_print:
            result = target.validate_proc_type_conventions(process, "App.custom.recipe")
        self.assertTrue(result)
        mock_print.assert_called_with(
            "App.custom.recipe: WARNING: Unknown recipe type. Skipping processor convention checks."
        )

    def test_validate_proc_type_conventions_known_type_wrong_processor_fails(self):
        # Munki processor in a download recipe should fail
        process = [{"Processor": "MunkiImporter"}]
        with mock.patch("builtins.print") as mock_print:
            result = target.validate_proc_type_conventions(
                process, "App.download.recipe"
            )
        self.assertFalse(result)
        mock_print.assert_called_with(
            "App.download.recipe: Processor MunkiImporter is not conventional for this recipe type."
        )

    def test_validate_proc_type_conventions_known_type_correct_processor_passes(self):
        # Munki processor in a munki recipe should pass
        process = [{"Processor": "MunkiImporter"}]
        result = target.validate_proc_type_conventions(process, "App.munki.recipe")
        self.assertTrue(result)

    def test_validate_required_proc_for_types_munki_with_importer_passes(self):
        # Munki recipe with MunkiImporter should pass
        process = [{"Processor": "MunkiImporter"}]
        result = target.validate_required_proc_for_types(process, "App.munki.recipe")
        self.assertTrue(result)

    def test_validate_required_proc_for_types_munki_without_importer_fails(self):
        # Munki recipe without MunkiImporter should fail
        process = [{"Processor": "URLDownloader"}]
        with mock.patch("builtins.print") as mock_print:
            result = target.validate_required_proc_for_types(
                process, "App.munki.recipe"
            )
        self.assertFalse(result)
        mock_print.assert_called_with(
            "App.munki.recipe: Recipe type munki should contain processor MunkiImporter."
        )

    def test_validate_required_proc_for_types_pkg_with_creator_passes(self):
        # Pkg recipe with PkgCreator should pass
        process = [{"Processor": "PkgCreator"}]
        result = target.validate_required_proc_for_types(process, "App.pkg.recipe")
        self.assertTrue(result)

    def test_validate_required_proc_for_types_pkg_without_creator_fails(self):
        # Pkg recipe without required processor should fail
        process = [{"Processor": "URLDownloader"}]
        with mock.patch("builtins.print") as mock_print:
            result = target.validate_required_proc_for_types(process, "App.pkg.recipe")
        self.assertFalse(result)
        mock_print.assert_called_with(
            "App.pkg.recipe: Recipe type pkg should contain one of these processors: ['AppPkgCreator', 'PkgCreator', 'PkgCopier']."
        )

    def test_validate_required_proc_for_types_pkg_empty_process_passes(self):
        # Pkg recipe with empty process list should pass (special case)
        process = []
        result = target.validate_required_proc_for_types(process, "App.pkg.recipe")
        self.assertTrue(result)

    def test_validate_required_proc_for_types_jss_with_importer_passes(self):
        # JSS recipe with JSSImporter should pass
        process = [{"Processor": "JSSImporter"}]
        result = target.validate_required_proc_for_types(process, "App.jss.recipe")
        self.assertTrue(result)

    def test_validate_required_proc_for_types_unknown_type_passes(self):
        # Unknown recipe type should pass (no checks)
        process = [{"Processor": "SomeProcessor"}]
        result = target.validate_required_proc_for_types(process, "App.unknown.recipe")
        self.assertTrue(result)

    def test_validate_proc_args_valid_arguments_passes(self):
        with mock.patch.object(
            target, "_CORE_PROCS", {"URLDownloader": {"url": {}, "filename": {}}}
        ):
            process = [
                {
                    "Processor": "URLDownloader",
                    "Arguments": {"url": "https://example.com/file.dmg"},
                }
            ]
            result = target.validate_proc_args(process, "App.download.recipe")
            self.assertTrue(result)

    def test_validate_proc_args_invalid_argument_fails(self):
        with mock.patch.object(
            target, "_CORE_PROCS", {"URLDownloader": {"url": {}, "filename": {}}}
        ), mock.patch("builtins.print") as mock_print:
            process = [
                {
                    "Processor": "URLDownloader",
                    "Arguments": {"invalid_arg": "value"},
                }
            ]
            result = target.validate_proc_args(process, "App.download.recipe")
            self.assertFalse(result)
            mock_print.assert_any_call(
                "App.download.recipe: Unknown argument invalid_arg for "
                "processor URLDownloader. Allowed arguments are: url, filename"
            )

    def test_validate_proc_args_invalid_argument_prints_suggestion(self):
        with mock.patch.object(
            target, "_CORE_PROCS", {"URLDownloader": {"url": {}, "filename": {}}}
        ), mock.patch("builtins.print") as mock_print:
            process = [
                {
                    "Processor": "URLDownloader",
                    "Arguments": {"invalid_arg": "value"},
                }
            ]
            target.validate_proc_args(process, "App.download.recipe")
            mock_print.assert_any_call(
                "Consider using the VariableSetter processor (AutoPkg 2.9.0+) "
                "to set custom environment variables."
            )

    def test_validate_proc_args_ignored_arguments_passes(self):
        with mock.patch.object(
            target, "_CORE_PROCS", {"URLDownloader": {"url": {}, "filename": {}}}
        ):
            process = [
                {
                    "Processor": "URLDownloader",
                    "Arguments": {
                        "url": "https://example.com/file.dmg",
                        "note": "This is a note",
                    },
                }
            ]
            result = target.validate_proc_args(process, "App.download.recipe")
            self.assertTrue(result)

    def test_validate_proc_args_non_core_processor_passes(self):
        with mock.patch.object(target, "_CORE_PROCS", {"URLDownloader": {}}):
            process = [
                {
                    "Processor": "com.github.custom.CustomProcessor",
                    "Arguments": {"any_arg": "value"},
                }
            ]
            result = target.validate_proc_args(process, "App.download.recipe")
            self.assertTrue(result)

    def test_validate_proc_args_processor_with_no_args_fails(self):
        with mock.patch.object(
            target, "_CORE_PROCS", {"StopProcessingIf": {}}
        ), mock.patch("builtins.print") as mock_print:
            process = [
                {
                    "Processor": "StopProcessingIf",
                    "Arguments": {"invalid_arg": "value"},
                }
            ]
            result = target.validate_proc_args(process, "App.download.recipe")
            self.assertFalse(result)
            mock_print.assert_any_call(
                "App.download.recipe: Unknown argument invalid_arg for processor "
                "StopProcessingIf, which does not accept any arguments."
            )

    def test_validate_proc_args_processor_with_no_args_prints_suggestion(self):
        with mock.patch.object(
            target, "_CORE_PROCS", {"StopProcessingIf": {}}
        ), mock.patch("builtins.print") as mock_print:
            process = [
                {
                    "Processor": "StopProcessingIf",
                    "Arguments": {"invalid_arg": "value"},
                }
            ]
            target.validate_proc_args(process, "App.download.recipe")
            mock_print.assert_any_call(
                "Consider using the VariableSetter processor (AutoPkg 2.9.0+) "
                "to set custom environment variables."
            )


if __name__ == "__main__":
    unittest.main()

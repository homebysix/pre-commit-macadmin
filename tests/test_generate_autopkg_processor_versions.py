import argparse
import ast
import subprocess
import tempfile
import unittest
from pathlib import Path

import scripts.generate_autopkg_processor_versions as generator
from pre_commit_macadmin_hooks.autopkg_processor_versions import PROC_VERSIONS


class TestGenerateAutoPkgProcessorVersions(unittest.TestCase):

    def run_git(self, repo, *args):
        return subprocess.run(
            ["git", "-C", str(repo), *args],
            check=True,
            encoding="utf-8",
            capture_output=True,
        )

    def init_repo(self, tmp_path):
        repo = tmp_path / "autopkg"
        repo.mkdir()
        self.run_git(repo, "init")
        self.run_git(repo, "config", "user.email", "tests@example.com")
        self.run_git(repo, "config", "user.name", "Tests")
        return repo

    def write_processor(
        self,
        repo,
        relative_path,
        class_name,
        args,
        introduced=None,
        deprecated=None,
    ):
        path = repo / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        arg_lines = "\n".join(
            f'        "{arg}": {{"required": False}},' for arg in args
        )
        lifecycle_line = []
        lifecycle_items = []
        if introduced:
            lifecycle_items.append(f'"introduced": "{introduced}"')
        if deprecated:
            lifecycle_items.append(f'"deprecated": "{deprecated}"')
        if lifecycle_items:
            lifecycle_line = [f"    lifecycle = {{{', '.join(lifecycle_items)}}}"]
        path.write_text(
            "\n".join(
                [
                    "from autopkglib import Processor",
                    "",
                    f"class {class_name}(Processor):",
                    *lifecycle_line,
                    "    input_variables = {",
                    arg_lines,
                    "    }",
                    "",
                ]
            ),
            encoding="utf-8",
        )

    def commit(self, repo, message):
        self.run_git(repo, "add", "-A")
        self.run_git(repo, "commit", "-m", message)

    def generate_text(self, repo, output_path, **overrides):
        args = argparse.Namespace(
            autopkg_repo=str(repo),
            output=str(output_path),
            baseline_ref=None,
            include_prereleases=False,
            full=True,
            incremental=False,
            check=False,
        )
        for key, value in overrides.items():
            setattr(args, key, value)
        generated, warnings = generator.generate(args)
        self.assertEqual(warnings, [])
        return generated

    def test_normalize_tag_version_accepts_bare_tags(self):
        self.assertEqual(generator.normalize_tag_version("v1.1")[0], "1.1")

    def test_fallback_parses_all_keys_from_python2_only_source(self):
        source = "\n".join(
            [
                "from autopkglib import Processor",
                "",
                "class ExampleProcessor(Processor):",
                "    input_variables = {",
                '        "url": {"required": True},',
                '        "download_dir": {"required": False},',
                '        "filename": {"required": False},',
                '        "PKG": {"required": False},',
                "    }",
                "",
                "    def main(self):",
                '        print "downloading"',
                "",
            ]
        )

        # Confirm this source needs the regex/tokenizer fallback, i.e. it
        # reproduces the conditions of the regression (Python-2-only syntax
        # that ast.parse cannot handle).
        with self.assertRaises(SyntaxError):
            ast.parse(source)

        info = generator.parse_processor_source(source)

        self.assertEqual(
            info["ExampleProcessor"].args,
            {"url", "download_dir", "filename", "PKG"},
        )

    def test_full_generation_detects_argument_added_after_file_move(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo = self.init_repo(tmp_path)
            output_path = tmp_path / "autopkg_processor_versions.py"

            self.write_processor(
                repo,
                "Code/autopkglib/ExampleProcessor.py",
                "ExampleProcessor",
                ["url"],
            )
            self.commit(repo, "Add baseline processor")
            self.run_git(repo, "tag", "v0.1.0")

            old_path = repo / "Code/autopkglib/ExampleProcessor.py"
            new_path = repo / "Source/autopkglib/ExampleProcessor.py"
            new_path.parent.mkdir(parents=True, exist_ok=True)
            old_path.rename(new_path)
            self.write_processor(
                repo,
                "Source/autopkglib/ExampleProcessor.py",
                "ExampleProcessor",
                ["url", "new_arg"],
            )
            self.commit(repo, "Move processor and add argument")
            self.run_git(repo, "tag", "v1.1")

            generated = self.generate_text(repo, output_path)

        self.assertIn('"ExampleProcessor": {', generated)
        self.assertIn('"_introduced_": "0.1.0"', generated)
        self.assertIn('"new_arg": "1.1"', generated)

    def test_lifecycle_introduced_overrides_git_first_seen(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo = self.init_repo(tmp_path)
            output_path = tmp_path / "autopkg_processor_versions.py"

            self.write_processor(
                repo,
                "Code/autopkglib/ExampleProcessor.py",
                "ExampleProcessor",
                ["url"],
                "1.0.0",
            )
            self.commit(repo, "Add processor with mismatched lifecycle")
            self.run_git(repo, "tag", "v0.1.0")

            args = argparse.Namespace(
                autopkg_repo=str(repo),
                output=str(output_path),
                baseline_ref=None,
                include_prereleases=False,
                full=True,
                incremental=False,
                check=False,
            )
            generated, warnings = generator.generate(args)

        self.assertIn('"_introduced_": "1.0.0"', generated)
        self.assertEqual(
            warnings,
            [
                "ExampleProcessor: overriding _introduced_ 0.1.0 "
                "with lifecycle introduced 1.0.0"
            ],
        )

    def test_lifecycle_deprecated_is_extracted(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo = self.init_repo(tmp_path)
            output_path = tmp_path / "autopkg_processor_versions.py"

            self.write_processor(
                repo,
                "Code/autopkglib/ExampleProcessor.py",
                "ExampleProcessor",
                ["url"],
                introduced="0.1.0",
                deprecated="1.0.0",
            )
            self.commit(repo, "Add deprecated processor")
            self.run_git(repo, "tag", "v0.1.0")

            generated = self.generate_text(repo, output_path)

        self.assertIn('"_introduced_": "0.1.0"', generated)
        self.assertIn('"_deprecated_": "1.0.0"', generated)

    def test_processor_disappearance_creates_removed_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo = self.init_repo(tmp_path)
            output_path = tmp_path / "autopkg_processor_versions.py"

            processor_path = "Code/autopkglib/ExampleProcessor.py"
            self.write_processor(
                repo,
                processor_path,
                "ExampleProcessor",
                ["url"],
            )
            self.commit(repo, "Add processor")
            self.run_git(repo, "tag", "v0.1.0")

            (repo / processor_path).unlink()
            self.commit(repo, "Remove processor")
            self.run_git(repo, "tag", "v1.0.0")

            generated = self.generate_text(repo, output_path)

        self.assertIn('"ExampleProcessor": {', generated)
        self.assertIn('"_removed_": "1.0.0"', generated)

    def test_exported_alias_counts_as_processor_presence(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo = self.init_repo(tmp_path)
            output_path = tmp_path / "autopkg_processor_versions.py"

            self.write_processor(
                repo,
                "Code/autopkglib/TargetProcessor.py",
                "TargetProcessor",
                ["url"],
            )
            self.write_processor(
                repo,
                "Code/autopkglib/LegacyProcessor.py",
                "LegacyProcessor",
                ["url"],
            )
            self.commit(repo, "Add processors")
            self.run_git(repo, "tag", "v0.1.0")

            alias_path = repo / "Code/autopkglib/LegacyProcessor.py"
            alias_path.write_text(
                "\n".join(
                    [
                        "from autopkglib.TargetProcessor import TargetProcessor",
                        "",
                        '__all__ = ["LegacyProcessor"]',
                        "LegacyProcessor = TargetProcessor",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            self.commit(repo, "Replace processor with compatibility alias")
            self.run_git(repo, "tag", "v1.0.0")

            generated = self.generate_text(repo, output_path)

        self.assertIn('"LegacyProcessor": {', generated)
        self.assertNotIn('"_removed_"', generated)

    def test_processor_reappearance_warns_and_clears_removed_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo = self.init_repo(tmp_path)
            output_path = tmp_path / "autopkg_processor_versions.py"

            processor_path = "Code/autopkglib/ExampleProcessor.py"
            self.write_processor(
                repo,
                processor_path,
                "ExampleProcessor",
                ["url"],
            )
            self.commit(repo, "Add processor")
            self.run_git(repo, "tag", "v0.1.0")

            (repo / processor_path).unlink()
            self.commit(repo, "Remove processor")
            self.run_git(repo, "tag", "v1.0.0")

            self.write_processor(
                repo,
                processor_path,
                "ExampleProcessor",
                ["url"],
            )
            self.commit(repo, "Re-add processor")
            self.run_git(repo, "tag", "v1.1.0")

            args = argparse.Namespace(
                autopkg_repo=str(repo),
                output=str(output_path),
                baseline_ref=None,
                include_prereleases=False,
                full=True,
                incremental=False,
                check=False,
            )
            generated, warnings = generator.generate(args)

        self.assertIn('"ExampleProcessor": {', generated)
        self.assertNotIn('"_removed_"', generated)
        self.assertEqual(
            warnings,
            [
                "ExampleProcessor: processor reappeared in 1.1.0 "
                "after being absent since 1.0.0"
            ],
        )

    def test_missing_baseline_tag_requires_baseline_ref(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo = self.init_repo(tmp_path)
            self.write_processor(
                repo,
                "Code/autopkglib/ExampleProcessor.py",
                "ExampleProcessor",
                ["url"],
            )
            self.commit(repo, "Add processor")
            self.run_git(repo, "tag", "v1.0.0")

            with self.assertRaises(ValueError):
                generator.public_releases(repo)

            releases = generator.public_releases(repo, baseline_ref="HEAD")

        self.assertEqual(releases[0].version, "0.1.0")
        self.assertEqual(releases[0].ref, "HEAD")

    def test_incremental_generation_appends_new_releases(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo = self.init_repo(tmp_path)
            output_path = tmp_path / "autopkg_processor_versions.py"

            self.write_processor(
                repo,
                "Code/autopkglib/FirstProcessor.py",
                "FirstProcessor",
                ["url"],
            )
            self.commit(repo, "Add first processor")
            self.run_git(repo, "tag", "v0.1.0")

            full_text = self.generate_text(repo, output_path)
            output_path.write_text(full_text, encoding="utf-8")

            self.write_processor(
                repo,
                "Code/autopkglib/SecondProcessor.py",
                "SecondProcessor",
                ["path"],
            )
            self.commit(repo, "Add second processor")
            self.run_git(repo, "tag", "v1.0.0")

            incremental_text = self.generate_text(
                repo,
                output_path,
                full=False,
                incremental=True,
            )

        self.assertIn('"FirstProcessor": {', incremental_text)
        self.assertIn('"SecondProcessor": {', incremental_text)
        self.assertIn('"_introduced_": "0.1.0"', incremental_text)
        self.assertIn('"_introduced_": "1.0.0"', incremental_text)
        self.assertIn('"last_walked_version": "1.0.0"', incremental_text)

    def test_generated_runtime_data_is_sorted(self):
        self.assertEqual(list(PROC_VERSIONS), sorted(PROC_VERSIONS))
        for versions in PROC_VERSIONS.values():
            self.assertEqual(next(iter(versions)), "_introduced_")
            metadata_keys = [
                key
                for key in versions
                if key in {"_introduced_", "_deprecated_", "_removed_"}
            ]
            self.assertEqual(
                metadata_keys,
                [
                    key
                    for key in ("_introduced_", "_deprecated_", "_removed_")
                    if key in versions
                ],
            )
            argument_keys = [
                key
                for key in versions
                if key not in {"_introduced_", "_deprecated_", "_removed_"}
            ]
            self.assertEqual(argument_keys, sorted(argument_keys))


if __name__ == "__main__":
    unittest.main()

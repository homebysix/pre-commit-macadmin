#!/usr/bin/python
"""Tests for the format_autopkg_yaml_recipes hook."""

import tempfile
import unittest
from pathlib import Path

import ruamel.yaml

from pre_commit_macadmin_hooks import format_autopkg_yaml_recipes


class TestFormatAutopkgYamlRecipes(unittest.TestCase):

    def setUp(self):
        self._paths = []

    def tearDown(self):
        for path in self._paths:
            Path(path).unlink(missing_ok=True)

    def _write(self, content: str) -> str:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".recipe.yaml", delete=False
        ) as tmp:
            tmp.write(content)
            self._paths.append(tmp.name)
            return tmp.name

    def _read(self, path: str) -> str:
        with open(path) as f:
            return f.read()

    def test_idempotent(self):
        path = self._write(
            "Identifier: com.example.test\n"
            "Description: A test recipe.\n"
            "Input:\n"
            "  NAME: TestApp\n"
            "Process:\n"
            "  - Processor: URLDownloader\n"
            "    Arguments:\n"
            "      url: https://example.com/file.dmg\n"
        )
        self.assertEqual(format_autopkg_yaml_recipes.main([path]), 0)
        once = self._read(path)
        self.assertEqual(format_autopkg_yaml_recipes.main([path]), 0)
        self.assertEqual(once, self._read(path))

    def test_top_level_key_reorder(self):
        path = self._write(
            "Process:\n"
            "  - Processor: EndOfCheckPhase\n"
            "Input:\n"
            "  NAME: TestApp\n"
            "Identifier: com.example.test\n"
            "Description: A test recipe.\n"
        )
        self.assertEqual(format_autopkg_yaml_recipes.main([path]), 0)
        text = self._read(path)
        order = [
            text.index("Description:"),
            text.index("Identifier:"),
            text.index("Input:"),
            text.index("Process:"),
        ]
        self.assertEqual(order, sorted(order))

    def test_input_name_moved_first(self):
        path = self._write(
            "Identifier: com.example.test\n"
            "Input:\n"
            "  DOWNLOAD_URL: https://example.com\n"
            "  NAME: TestApp\n"
            "  VERSION: '1.0'\n"
        )
        self.assertEqual(format_autopkg_yaml_recipes.main([path]), 0)
        text = self._read(path)
        input_idx = text.index("Input:")
        name_idx = text.index("NAME:", input_idx)
        url_idx = text.index("DOWNLOAD_URL:", input_idx)
        self.assertLess(name_idx, url_idx)

    def test_processor_arguments_moved_last(self):
        path = self._write(
            "Identifier: com.example.test\n"
            "Process:\n"
            "  - Arguments:\n"
            "      url: https://example.com/file.dmg\n"
            "    Comment: Download the thing.\n"
            "    Processor: URLDownloader\n"
        )
        self.assertEqual(format_autopkg_yaml_recipes.main([path]), 0)
        text = self._read(path)
        proc_idx = text.index("Processor:")
        comment_idx = text.index("Comment:", proc_idx)
        args_idx = text.index("Arguments:", proc_idx)
        self.assertLess(proc_idx, comment_idx)
        self.assertLess(comment_idx, args_idx)

    def test_blank_line_before_process_but_not_before_first_processor(self):
        path = self._write(
            "Identifier: com.example.test\n"
            "Input:\n"
            "  NAME: TestApp\n"
            "Process:\n"
            "  - Processor: EndOfCheckPhase\n"
        )
        self.assertEqual(format_autopkg_yaml_recipes.main([path]), 0)
        lines = self._read(path).split("\n")
        process_idx = lines.index("Process:")
        self.assertEqual(lines[process_idx - 1], "")
        self.assertTrue(lines[process_idx + 1].startswith("- Processor:"))

    def test_yes_no_strings_preserved(self):
        path = self._write(
            "Identifier: com.example.test\n"
            "Input:\n"
            "  NAME: TestApp\n"
            "  DERIVE_MIN_OS: 'YES'\n"
            "  SOMETHING_ELSE: 'NO'\n"
        )
        self.assertEqual(format_autopkg_yaml_recipes.main([path]), 0)
        text = self._read(path)
        self.assertIn("'YES'", text)
        self.assertIn("'NO'", text)
        yaml = ruamel.yaml.YAML(typ="safe")
        with open(path) as f:
            data = yaml.load(f)
        self.assertEqual(data["Input"]["DERIVE_MIN_OS"], "YES")
        self.assertIsInstance(data["Input"]["DERIVE_MIN_OS"], str)

    def test_comments_preserved(self):
        path = self._write(
            "Identifier: com.example.test  # the recipe id\n"
            "Input:\n"
            "  NAME: TestApp\n"
        )
        self.assertEqual(format_autopkg_yaml_recipes.main([path]), 0)
        self.assertIn("# the recipe id", self._read(path))

    def test_comments_realigned_to_reindented_process(self):
        # Process list indented 4 spaces; the formatter re-emits the dash at
        # column 0, and the comment-only lines must follow the new indentation
        # rather than keep their original absolute columns.
        path = self._write(
            "Identifier: com.example.test\n"
            "Process:\n"
            "    # comment before first processor\n"
            "    - Processor: URLDownloader\n"
            "      Arguments:\n"
            "        # comment about url\n"
            "        url: https://example.com/file.dmg\n"
            "    # comment before second processor\n"
            "    - Processor: EndOfCheckPhase\n"
        )
        self.assertEqual(format_autopkg_yaml_recipes.main([path]), 0)
        lines = self._read(path).split("\n")
        # Comments before a processor align with the dash (column 0).
        self.assertIn("# comment before first processor", lines)
        self.assertIn("# comment before second processor", lines)
        # The comment inside Arguments aligns with its sibling key (column 4).
        self.assertIn("    # comment about url", lines)
        self.assertIn("    url: https://example.com/file.dmg", lines)

    def test_no_blank_line_before_processor_keeps_comment_tight(self):
        # With the flag, no blank line is inserted before "- Processor:", so a
        # comment stays directly above the processor it documents.
        path = self._write(
            "Identifier: com.example.test\n"
            "Process:\n"
            "    # download the app\n"
            "    - Processor: URLDownloader\n"
            "      Arguments:\n"
            "        url: https://example.com/file.dmg\n"
            "    # end the check phase\n"
            "    - Processor: EndOfCheckPhase\n"
        )
        self.assertEqual(
            format_autopkg_yaml_recipes.main(
                ["--no-blank-line-before-processor", path]
            ),
            0,
        )
        lines = self._read(path).split("\n")
        # No blank line between the comment and its processor.
        first = lines.index("# download the app")
        self.assertEqual(lines[first + 1], "- Processor: URLDownloader")
        second = lines.index("# end the check phase")
        self.assertEqual(lines[second + 1], "- Processor: EndOfCheckPhase")

    def test_blank_line_before_processor_is_default(self):
        # Without the flag, the default behavior still inserts a blank line
        # before non-first "- Processor:" entries.
        path = self._write(
            "Identifier: com.example.test\n"
            "Process:\n"
            "  - Processor: URLDownloader\n"
            "  - Processor: EndOfCheckPhase\n"
        )
        self.assertEqual(format_autopkg_yaml_recipes.main([path]), 0)
        lines = self._read(path).split("\n")
        second = lines.index("- Processor: EndOfCheckPhase")
        self.assertEqual(lines[second - 1], "")

    def test_invalid_yaml_returns_one(self):
        path = self._write("Identifier: com.example.test\n  : : bad\n")
        self.assertEqual(format_autopkg_yaml_recipes.main([path]), 1)

    def test_multiple_files(self):
        path1 = self._write("Identifier: com.example.one\nInput:\n  NAME: One\n")
        path2 = self._write("Identifier: com.example.two\nInput:\n  NAME: Two\n")
        self.assertEqual(format_autopkg_yaml_recipes.main([path1, path2]), 0)
        self.assertIn("com.example.one", self._read(path1))
        self.assertIn("com.example.two", self._read(path2))

    def test_already_formatted_does_not_rewrite(self):
        path = self._write(
            "Identifier: com.example.test\n" "Input:\n" "  NAME: TestApp\n"
        )
        self.assertEqual(format_autopkg_yaml_recipes.main([path]), 0)
        mtime_after_first = Path(path).stat().st_mtime_ns
        self.assertEqual(format_autopkg_yaml_recipes.main([path]), 0)
        self.assertEqual(Path(path).stat().st_mtime_ns, mtime_after_first)


if __name__ == "__main__":
    unittest.main()

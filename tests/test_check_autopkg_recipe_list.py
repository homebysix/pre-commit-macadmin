"""test_check_autopkg_recipe_list.py

Unit tests for the functions in check_autopkg_recipe_list.py."""

import io
import os
import plistlib
import sys
import tempfile
import unittest

import pre_commit_hooks.check_autopkg_recipe_list as target


class TestCheckAutopkgRecipeList(unittest.TestCase):
    def run_main_with_files(self, files):
        # Helper to run main() with given files and capture stdout
        sys_stdout = sys.stdout
        out = io.StringIO()
        sys.stdout = out
        try:
            retval = target.main(files)
        finally:
            sys.stdout = sys_stdout
        return retval, out.getvalue()

    def test_build_argument_parser_returns_parser(self):
        parser = target.build_argument_parser()
        args = parser.parse_args(["foo.txt", "bar.plist"])
        self.assertEqual(args.filenames, ["foo.txt", "bar.plist"])

    def test_txt_valid_recipe_list(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            txt = os.path.join(tmpdir, "recipes.txt")
            with open(txt, "w", encoding="utf-8") as f:
                f.write("com.example.recipe1\ncom.example.recipe2\n")
            retval, output = self.run_main_with_files([txt])
            self.assertEqual(retval, 0)
            self.assertEqual(output, "")

    def test_txt_invalid_recipe_list(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            txt = os.path.join(tmpdir, "recipes.txt")
            with open(txt, "w", encoding="utf-8") as f:
                f.write("# comment only\n\n")
            retval, output = self.run_main_with_files([txt])
            self.assertEqual(retval, 1)
            self.assertIn("invalid recipe list", output)

    def test_plist_valid_recipe_list(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            plist = os.path.join(tmpdir, "recipes.plist")
            data = {"recipes": ["com.example.recipe1", "com.example.recipe2"]}
            with open(plist, "wb") as f:
                plistlib.dump(data, f)
            retval, output = self.run_main_with_files([plist])
            self.assertEqual(retval, 0)
            self.assertEqual(output, "")

    def test_plist_invalid_recipe_list(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            plist = os.path.join(tmpdir, "recipes.plist")
            with open(plist, "wb") as f:
                f.write(b"not a plist")
            retval, output = self.run_main_with_files([plist])
            self.assertEqual(retval, 1)
            self.assertTrue(
                "plist parsing error" in output or "invalid recipe list" in output
            )

    def test_yaml_valid_recipe_list(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_file = os.path.join(tmpdir, "recipes.yaml")
            with open(yaml_file, "w", encoding="utf-8") as f:
                f.write("- com.example.recipe1\n- com.example.recipe2\n")
            retval, output = self.run_main_with_files([yaml_file])
            self.assertEqual(retval, 0)
            self.assertEqual(output, "")

    def test_yaml_invalid_recipe_list(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_file = os.path.join(tmpdir, "recipes.yaml")
            with open(yaml_file, "w", encoding="utf-8") as f:
                f.write("not: a list")
            retval, output = self.run_main_with_files([yaml_file])
            self.assertEqual(retval, 1)
            self.assertIn("invalid recipe list", output)

    def test_json_valid_recipe_list(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            json_file = os.path.join(tmpdir, "recipes.json")
            with open(json_file, "w", encoding="utf-8") as f:
                f.write('["com.example.recipe1", "com.example.recipe2"]')
            retval, output = self.run_main_with_files([json_file])
            self.assertEqual(retval, 0)
            self.assertEqual(output, "")

    def test_json_invalid_recipe_list(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            json_file = os.path.join(tmpdir, "recipes.json")
            with open(json_file, "w", encoding="utf-8") as f:
                f.write('{"not": "a list"}')
            retval, output = self.run_main_with_files([json_file])
            self.assertEqual(retval, 1)
            self.assertIn("invalid recipe list", output)

    def test_makecatalogs_should_be_last(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            txt = os.path.join(tmpdir, "recipes.txt")
            with open(txt, "w", encoding="utf-8") as f:
                f.write("com.example.recipe.munki\nSomeOtherRecipe\nMakeCatalogs\n")
            retval, output = self.run_main_with_files([txt])
            self.assertEqual(retval, 0)
            self.assertEqual(output, "")

            txt2 = os.path.join(tmpdir, "recipes2.txt")
            with open(txt2, "w", encoding="utf-8") as f:
                f.write("com.example.recipe.munki\nMakeCatalogs\nSomeOtherRecipe\n")
            retval, output = self.run_main_with_files([txt2])
            self.assertEqual(retval, 1)
            self.assertIn("MakeCatalogs should be the last item", output)

    def test_nonexistent_file(self):
        with self.assertRaises(FileNotFoundError):
            self.run_main_with_files(["nonexistent/file.txt"])

    def test_multiple_files_mixed_valid_and_invalid(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Valid txt
            txt = os.path.join(tmpdir, "recipes.txt")
            with open(txt, "w", encoding="utf-8") as f:
                f.write("com.example.recipe1\ncom.example.recipe2\n")
            # Invalid yaml (not a list)
            yaml_file = os.path.join(tmpdir, "recipes.yaml")
            with open(yaml_file, "w", encoding="utf-8") as f:
                f.write("not: a list")
            # Valid json
            json_file = os.path.join(tmpdir, "recipes.json")
            with open(json_file, "w", encoding="utf-8") as f:
                f.write('["com.example.recipe1", "com.example.recipe2"]')
            retval, output = self.run_main_with_files([txt, yaml_file, json_file])
            self.assertEqual(retval, 1)
            self.assertIn("invalid recipe list", output)
            self.assertNotIn("plist parsing error", output)

    def test_empty_txt_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            txt = os.path.join(tmpdir, "empty.txt")
            with open(txt, "w", encoding="utf-8") as f:
                f.write("")
            retval, output = self.run_main_with_files([txt])
            self.assertEqual(retval, 1)
            self.assertIn("invalid recipe list", output)

    def test_txt_file_with_comments_and_blank_lines(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            txt = os.path.join(tmpdir, "comments.txt")
            with open(txt, "w", encoding="utf-8") as f:
                f.write("# comment\n\n# another\ncom.example.recipe\n\n")
            retval, output = self.run_main_with_files([txt])
            self.assertEqual(retval, 0)
            self.assertEqual(output, "")

    def test_yaml_parsing_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_file = os.path.join(tmpdir, "bad.yaml")
            with open(yaml_file, "w", encoding="utf-8") as f:
                f.write(":\n-")
            retval, output = self.run_main_with_files([yaml_file])
            self.assertEqual(retval, 1)
            self.assertIn("yaml parsing error", output)

    def test_json_parsing_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            json_file = os.path.join(tmpdir, "bad.json")
            with open(json_file, "w", encoding="utf-8") as f:
                f.write("{not a valid json")
            retval, output = self.run_main_with_files([json_file])
            self.assertEqual(retval, 1)
            self.assertIn("json parsing error", output)

    def test_plist_missing_recipes_key(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            plist = os.path.join(tmpdir, "missing_recipes.plist")
            data = {"notrecipes": ["foo", "bar"]}
            with open(plist, "wb") as f:
                plistlib.dump(data, f)
            retval, output = self.run_main_with_files([plist])
            self.assertEqual(retval, 1)
            self.assertIn("invalid recipe list", output)

    def test_makecatalogs_missing_when_munki_present(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            txt = os.path.join(tmpdir, "recipes.txt")
            with open(txt, "w", encoding="utf-8") as f:
                f.write("com.example.recipe.munki\nSomeOtherRecipe\n")
            retval, output = self.run_main_with_files([txt])
            self.assertEqual(retval, 1)
            self.assertIn("MakeCatalogs should be the last item", output)


if __name__ == "__main__":
    unittest.main()

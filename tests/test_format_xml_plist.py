#!/usr/bin/python
"""Tests for the format_xml_plist hook."""

import plistlib
import tempfile
import unittest
from pathlib import Path

from pre_commit_macadmin_hooks import format_xml_plist


class TestFormatXMLPlist(unittest.TestCase):
    """Tests for the format_xml_plist hook."""

    def test_format_valid_xml_plist(self):
        """Test formatting a valid XML plist."""
        test_data = {"key1": "value1", "key2": 123, "key3": ["a", "b", "c"]}

        with tempfile.NamedTemporaryFile(
            mode="wb", suffix=".plist", delete=False
        ) as tmp:
            # Write plist in XML format
            plistlib.dump(test_data, tmp, fmt=plistlib.FMT_XML)
            tmp_path = tmp.name

        try:
            # Run the formatter
            result = format_xml_plist.main([tmp_path])

            # Should succeed
            self.assertEqual(result, 0)

            # Verify the file can still be read and contains the same data
            with open(tmp_path, "rb") as f:
                formatted_data = plistlib.load(f)
            self.assertEqual(formatted_data, test_data)
        finally:
            Path(tmp_path).unlink()

    def test_format_binary_plist(self):
        """Test formatting a binary plist converts it to XML."""
        test_data = {"key1": "value1", "key2": 456}

        with tempfile.NamedTemporaryFile(
            mode="wb", suffix=".plist", delete=False
        ) as tmp:
            # Write plist in binary format
            plistlib.dump(test_data, tmp, fmt=plistlib.FMT_BINARY)
            tmp_path = tmp.name

        try:
            # Run the formatter
            result = format_xml_plist.main([tmp_path])

            # Should succeed
            self.assertEqual(result, 0)

            # Verify the file is now XML format
            with open(tmp_path, "rb") as f:
                content = f.read()
                # XML plists start with <?xml
                self.assertTrue(content.startswith(b"<?xml"))

            # Verify data integrity
            with open(tmp_path, "rb") as f:
                formatted_data = plistlib.load(f)
            self.assertEqual(formatted_data, test_data)
        finally:
            Path(tmp_path).unlink()

    def test_format_invalid_plist(self):
        """Test that invalid plists return an error."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".plist", delete=False
        ) as tmp:
            tmp.write("This is not a valid plist")
            tmp_path = tmp.name

        try:
            # Run the formatter
            result = format_xml_plist.main([tmp_path])

            # Should fail
            self.assertEqual(result, 1)
        finally:
            Path(tmp_path).unlink()

    def test_format_multiple_files(self):
        """Test formatting multiple plist files."""
        test_data_1 = {"file": "first"}
        test_data_2 = {"file": "second"}

        with tempfile.NamedTemporaryFile(
            mode="wb", suffix=".plist", delete=False
        ) as tmp1:
            plistlib.dump(test_data_1, tmp1, fmt=plistlib.FMT_XML)
            tmp1_path = tmp1.name

        with tempfile.NamedTemporaryFile(
            mode="wb", suffix=".plist", delete=False
        ) as tmp2:
            plistlib.dump(test_data_2, tmp2, fmt=plistlib.FMT_BINARY)
            tmp2_path = tmp2.name

        try:
            # Run the formatter on both files
            result = format_xml_plist.main([tmp1_path, tmp2_path])

            # Should succeed
            self.assertEqual(result, 0)

            # Verify both files
            with open(tmp1_path, "rb") as f:
                data1 = plistlib.load(f)
            with open(tmp2_path, "rb") as f:
                data2 = plistlib.load(f)

            self.assertEqual(data1, test_data_1)
            self.assertEqual(data2, test_data_2)
        finally:
            Path(tmp1_path).unlink()
            Path(tmp2_path).unlink()


if __name__ == "__main__":
    unittest.main()

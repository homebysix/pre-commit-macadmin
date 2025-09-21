import os
import tempfile
import unittest
from unittest import mock

import pre_commit_macadmin_hooks.check_jamf_extension_attributes as target


class TestCheckJamfExtensionAttributes(unittest.TestCase):
    def setUp(self):
        self.valid_content = "#!/bin/bash\n<result>OK</result>"
        self.missing_result = "#!/bin/bash\necho 'no result tags'"
        self.incomplete_result = "#!/bin/bash\n<result>missing close"
        self.invalid_shebang = "echo 'no shebang'\n<result>OK</result>"

    def test_argument_parser(self):
        parser = target.build_argument_parser()
        args = parser.parse_args(["file1", "file2", "--valid-shebangs", "#!/bin/bash"])
        self.assertEqual(args.filenames, ["file1", "file2"])
        self.assertEqual(args.valid_shebangs, ["#!/bin/bash"])

    @mock.patch(
        "pre_commit_macadmin_hooks.check_jamf_extension_attributes.validate_shebangs",
        return_value=True,
    )
    def test_valid_file(self, mock_validate):
        with tempfile.NamedTemporaryFile("w+", delete=False) as tf:
            tf.write(self.valid_content)
            tf.flush()
            retval = target.main([tf.name])
        os.unlink(tf.name)
        self.assertEqual(retval, 0)

    @mock.patch(
        "pre_commit_macadmin_hooks.check_jamf_extension_attributes.validate_shebangs",
        return_value=True,
    )
    def test_missing_result_tags(self, mock_validate):
        with tempfile.NamedTemporaryFile("w+", delete=False) as tf:
            tf.write(self.missing_result)
            tf.flush()
            with mock.patch("builtins.print") as mock_print:
                retval = target.main([tf.name])
        os.unlink(tf.name)
        self.assertEqual(retval, 1)
        mock_print.assert_any_call(f"{tf.name}: missing <result> and/or </result> tags")

    @mock.patch(
        "pre_commit_macadmin_hooks.check_jamf_extension_attributes.validate_shebangs",
        return_value=False,
    )
    def test_invalid_shebang(self, mock_validate):
        with tempfile.NamedTemporaryFile("w+", delete=False) as tf:
            tf.write(self.invalid_shebang)
            tf.flush()
            with mock.patch("builtins.print") as mock_print:
                retval = target.main([tf.name])
        os.unlink(tf.name)
        self.assertEqual(retval, 1)
        mock_print.assert_any_call(f"{tf.name}: does not start with a valid shebang")

    @mock.patch(
        "pre_commit_macadmin_hooks.check_jamf_extension_attributes.validate_shebangs",
        return_value=True,
    )
    def test_multiple_files_mixed_results(self, mock_validate):
        with tempfile.NamedTemporaryFile(
            "w+", delete=False
        ) as tf1, tempfile.NamedTemporaryFile("w+", delete=False) as tf2:
            tf1.write(self.valid_content)
            tf1.flush()
            tf2.write(self.missing_result)
            tf2.flush()
            with mock.patch("builtins.print") as mock_print:
                retval = target.main([tf1.name, tf2.name])
        os.unlink(tf1.name)
        os.unlink(tf2.name)
        self.assertEqual(retval, 1)
        mock_print.assert_any_call(
            f"{tf2.name}: missing <result> and/or </result> tags"
        )

    @mock.patch(
        "pre_commit_macadmin_hooks.check_jamf_extension_attributes.validate_shebangs",
        return_value=True,
    )
    def test_no_filenames(self, mock_validate):
        retval = target.main([])
        self.assertEqual(retval, 0)

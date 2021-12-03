#!/usr/bin/python
# -*- coding: utf-8 -*-
"""This hook checks ProfileCreator manifest plists for inconsistencies and common issues."""

import argparse
import plistlib
import sys
from datetime import datetime
from xml.parsers.expat import ExpatError

from pre_commit_hooks.util import validate_required_keys


def build_argument_parser():
    """Build and return the argument parser."""

    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("filenames", nargs="*", help="Filenames to check.")
    return parser


def validate_manifest_key_types(manifest, filename):
    """Validation of manifest key types.

    Used for AutoPkg- and Munki-related hooks.
    """

    # Remap string type to support unicode in both Python 2 and 3
    string = basestring if sys.version_info.major == 2 else str

    # manifest keys and their known types. Omitted keys are left unvalidated.
    # Last updated 2021-12-03.
    key_types = {
        "pfm_description_reference": string,
        "pfm_description": string,
        "pfm_domain": string,
        "pfm_format_version": int,
        "pfm_format": string,
        "pfm_last_modified": datetime,
        "pfm_name": string,
        "pfm_note": string,
        "pfm_platforms": list,
        "pfm_require": string,
        "pfm_subkeys": list,
        "pfm_targets": list,
        "pfm_title": string,
        "pfm_type": string,
        "pfm_unique": bool,
        "pfm_version": int,
    }

    passed = True
    for manifest_key, expected_type in key_types.items():
        if manifest_key in manifest:
            if not isinstance(manifest[manifest_key], expected_type):
                print(
                    "{}: manifest key {} should be type {}, not type {}".format(
                        filename,
                        manifest_key,
                        expected_type,
                        type(manifest[manifest_key]),
                    )
                )
                passed = False

    return passed


def main(argv=None):
    """Main process."""

    # Parse command line arguments.
    argparser = build_argument_parser()
    args = argparser.parse_args(argv)

    retval = 0
    for filename in args.filenames:
        try:
            with open(filename, "rb") as openfile:
                manifest = plistlib.load(openfile)
        except (ExpatError, ValueError) as err:
            print("{}: plist parsing error: {}".format(filename, err))
            retval = 1

    return retval


if __name__ == "__main__":
    exit(main())

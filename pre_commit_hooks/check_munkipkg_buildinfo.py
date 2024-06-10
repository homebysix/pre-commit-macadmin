#!/usr/bin/python
"""Check MunkiPkg build-info files to ensure they are valid."""

import argparse
import json
import plistlib
import sys
from xml.parsers.expat import ExpatError

import ruamel.yaml
from pre_commit_hooks.util import validate_required_keys

yaml = ruamel.yaml.YAML(typ="safe")


def build_argument_parser():
    """Build and return the argument parser."""

    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--identifier-prefix",
        default="",
        help="Expected prefix for package bundle identifiers.",
    )
    parser.add_argument("filenames", nargs="*", help="Filenames to check.")
    return parser


def validate_buildinfo_key_types(buildinfo, filename):
    """Ensure build-info files contain the proper types."""

    # Remap string type to support unicode in both Python 2 and 3
    # DEPRECATED: Python 2 support will be removed in the future
    string = basestring if sys.version_info.major == 2 else str

    # Pkginfo keys and their known types. Omitted keys are left unvalidated.
    # Source: https://github.com/munki/munki-pkg
    # Last updated 2019-06-27.
    buildinfo_types = {
        "distribution_style": bool,
        "identifier": string,
        "install_location": string,
        "name": string,
        "ownership": string,
        "postinstall_action": string,
        "preserve_xattr": bool,
        "product id": string,
        "signing_info": dict,
        "suppress_bundle_relocation": bool,
        "version": string,
    }

    passed = True
    for buildinfo_key, expected_type in buildinfo_types.items():
        if buildinfo_key in buildinfo:
            if not isinstance(buildinfo[buildinfo_key], expected_type):
                print(
                    f"{filename}: buildinfo key {buildinfo_key} should be type "
                    f"{expected_type}, not type {type(buildinfo[buildinfo_key])}"
                )
                passed = False

    return passed


def main(argv=None):
    """Main process."""

    # Parse command line arguments.
    argparser = build_argument_parser()
    args = argparser.parse_args(argv)

    retval = 0
    buildinfo = {}
    for filename in args.filenames:
        if filename.endswith(".plist"):
            try:
                with open(filename, "rb") as openfile:
                    buildinfo = plistlib.load(openfile)
            except (ExpatError, ValueError) as err:
                print(f"{filename}: plist parsing error: {err}")
                retval = 1
                break  # no need to continue testing this file
        elif filename.endswith((".yaml", ".yml")):
            try:
                with open(filename, encoding="utf-8") as openfile:
                    buildinfo = yaml.load(openfile)
            except Exception as err:
                print(f"{filename}: yaml parsing error: {err}")
                retval = 1
                break  # no need to continue testing this file
        elif filename.endswith(".json"):
            try:
                with open(filename, encoding="utf-8") as openfile:
                    buildinfo = json.load(openfile)
            except Exception as err:
                print(f"{filename}: json parsing error: {err}")
                retval = 1
                break  # no need to continue testing this file

        if not buildinfo or not isinstance(buildinfo, dict):
            print(f"{filename}: cannot parse build-info file")
            retval = 1
            break

        # Top level keys that all build-info files should contain.
        # NOTE: Even though other keys are listed as non-"optional" in the documentation,
        # name and version appear to be the only ones that are actually required.
        required_keys = ("name", "version")
        if not validate_required_keys(buildinfo, filename, required_keys):
            retval = 1
            break  # No need to continue checking this file

        if args.identifier_prefix:
            # Warn if the identifier does not start with the expected prefix.
            if not buildinfo.get("identifier", "").startswith(args.identifier_prefix):
                print(
                    f"{filename}: identifier does not start with {args.identifier_prefix}."
                )
                retval = 1

        # Ensure buildinfo keys have expected types.
        if not validate_buildinfo_key_types(buildinfo, filename):
            retval = 1

        # Warn if install_location is not the startup disk.
        if buildinfo.get("install_location") != "/":
            print(
                f"{filename}: WARNING: install_location is not set to the startup disk."
            )

    return retval


if __name__ == "__main__":
    exit(main())

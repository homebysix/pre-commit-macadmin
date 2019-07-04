#!/usr/bin/python
"""Check MunkiPkg build-info files to ensure they are valid."""

import argparse
import plistlib
from xml.parsers.expat import ExpatError
import json
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

    # Remap basestring in Python 3
    # Credit: https://github.com/munki/munki/blob/ff6248daafa527def0fd109e0c72c69ca179702c
    # /code/client/munkilib/wrappers.py#L121-L125
    try:
        _ = basestring
    except NameError:
        basestring = str  # pylint: disable=W0622

    # Pkginfo keys and their known types. Omitted keys are left unvalidated.
    # Source: https://github.com/munki/munki-pkg
    # Last updated 2019-06-27.
    buildinfo_types = {
        "distribution_style": bool,
        "identifier": basestring,
        "install_location": basestring,
        "name": basestring,
        "ownership": basestring,
        "postinstall_action": basestring,
        "preserve_xattr": bool,
        "product id": basestring,
        "signing_info": dict,
        "suppress_bundle_relocation": bool,
        "version": basestring,
    }

    passed = True
    for buildinfo_key, expected_type in buildinfo_types.items():
        if buildinfo_key in buildinfo:
            if not isinstance(buildinfo[buildinfo_key], expected_type):
                print(
                    "{}: buildinfo key {} should be type {}, not type {}".format(
                        filename,
                        buildinfo_key,
                        expected_type,
                        type(buildinfo[buildinfo_key]),
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
    buildinfo = {}
    for filename in args.filenames:
        if filename.endswith(".plist"):
            try:
                buildinfo = plistlib.readPlist(filename)
            except (ExpatError, ValueError) as err:
                print("{}: plist parsing error: {}".format(filename, err))
                retval = 1
                break  # no need to continue testing this file
        elif filename.endswith((".yaml", ".yml")):
            try:
                with open(filename, "r") as openfile:
                    buildinfo = yaml.load(openfile)
            except Exception as err:
                print("{}: yaml parsing error: {}".format(filename, err))
                retval = 1
                break  # no need to continue testing this file
        elif filename.endswith(".json"):
            try:
                with open(filename, "r") as openfile:
                    buildinfo = json.load(openfile)
            except Exception as err:
                print("{}: json parsing error: {}".format(filename, err))
                retval = 1
                break  # no need to continue testing this file

        if not buildinfo or not isinstance(buildinfo, dict):
            print("{}: cannot parse build-info file".format(filename))
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
                    "{}: identifier does not start "
                    "with {}.".format(filename, args.identifier_prefix)
                )
                retval = 1

        # Ensure buildinfo keys have expected types.
        if not validate_buildinfo_key_types(buildinfo, filename):
            retval = 1

        # Warn if install_location is not the startup disk.
        if buildinfo.get("install_location") != "/":
            print(
                "{}: WARNING: install_location is not set to the "
                "startup disk.".format(filename)
            )

    return retval


if __name__ == "__main__":
    exit(main())

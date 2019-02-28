#!/usr/bin/python
"""This hook checks AutoPkg recipes to ensure they contain required top-level keys.
(https://github.com/autopkg/autopkg/wiki/Recipe-Format)."""

import argparse
import plistlib
from xml.parsers.expat import ExpatError


def build_argument_parser():
    """Build and return the argument parser."""

    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--override-prefix",
        default="local",
        help='Expected prefix for recipe override identifiers. (e.g. "com.yourcompany")',
    )
    parser.add_argument("filenames", nargs="*", help="Filenames to check.")
    return parser


def main(argv=None):
    """Main process."""

    # Top level keys that all AutoPkg recipes should contain.
    required_keys = ("Identifier", "Input")

    # Parse command line arguments.
    argparser = build_argument_parser()
    args = argparser.parse_args(argv)

    retval = 0
    for filename in args.filenames:
        try:
            recipe = plistlib.readPlist(filename)
            for req_key in required_keys:
                if req_key not in recipe:
                    print("{}: missing required key {}".format(filename, req_key))
                    retval = 1
                    break  # No need to continue checking this file

        except (ExpatError, ValueError) as err:
            print("{}: plist parsing error: {}".format(filename, err))
            retval = 1

        if args.override_prefix and "Process" not in recipe:
            override_prefix = args.override_prefix.rstrip(".")
            if not recipe.get("Identifier", "").startswith(override_prefix):
                print(
                    '{}: identifier does not start with "{}."'.format(
                        filename, override_prefix
                    )
                )
                retval = 1

    return retval


if __name__ == "__main__":
    exit(main())

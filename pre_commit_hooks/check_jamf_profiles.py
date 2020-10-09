#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Check Jamf scripts for common issues."""

import argparse
import plistlib
from xml.parsers.expat import ExpatError


def build_argument_parser():
    """Build and return the argument parser."""

    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("filenames", nargs="*", help="Filenames to check.")
    return parser


def main(argv=None):
    """Main process."""

    # Parse command line arguments.
    argparser = build_argument_parser()
    args = argparser.parse_args(argv)

    retval = 0
    for filename in args.filenames:
        try:
            with open(filename, "rb") as openfile:
                profile = plistlib.load(openfile)
        except (ExpatError, ValueError) as err:
            print("{}: plist parsing error: {}".format(filename, err))
            retval = 1

    return retval


if __name__ == "__main__":
    exit(main())

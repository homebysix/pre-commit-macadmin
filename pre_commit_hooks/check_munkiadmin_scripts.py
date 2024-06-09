#!/usr/bin/python
# -*- coding: utf-8 -*-
"""This hook ensures MunkiAdmin scripts are executable."""

import argparse
import os

from util import validate_shebangs


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

        # Ensure scripts are executable
        if not os.access(filename, os.X_OK):
            print(f"{filename}: not executable")
            retval = 1

        # Ensure scripts have a proper shebang
        with open(filename, "r", encoding="utf-8") as openfile:
            script_content = openfile.read()
        if not validate_shebangs(script_content, filename):
            print(f"{filename}: does not start with a valid shebang")
            retval = 1

    return retval


if __name__ == "__main__":
    exit(main())

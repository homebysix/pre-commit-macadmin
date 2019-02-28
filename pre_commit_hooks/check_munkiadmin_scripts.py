#!/usr/bin/python
"""This hook ensures MunkiAdmin scripts are executable."""

import argparse
import os


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
        if not os.access(filename, os.X_OK):
            print("{}: not executable".format(filename))
            retval = 1

    return retval


if __name__ == "__main__":
    exit(main())

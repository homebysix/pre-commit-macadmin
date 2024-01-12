#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Check Jamf extension attributes for common issues."""

import argparse
import re


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
        with open(filename, "r", encoding="utf-8") as openfile:
            ea_content = openfile.read()

        if "<result>" not in ea_content or "</result>" not in ea_content:
            print(f"{filename}: missing <result> and/or </result> tags")
            retval = 1
        all_results = len(re.findall("result.*\/result", ea_content))
        proper_results = len(re.findall("<result>.*<\/result>", ea_content))
        if proper_results < all_results:
            print(f"{filename}: has incomplete <result> tags!")

    return retval


if __name__ == "__main__":
    exit(main())

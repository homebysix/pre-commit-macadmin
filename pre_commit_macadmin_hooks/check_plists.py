#!/usr/bin/python
"""This hook checks XML property list (plist) files for basic syntax errors."""

import argparse
import plistlib
from typing import List, Optional
from xml.parsers.expat import ExpatError


def build_argument_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser."""

    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("filenames", nargs="*", help="Filenames to check.")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Main process."""

    # Parse command line arguments.
    argparser = build_argument_parser()
    args = argparser.parse_args(argv)

    retval = 0
    for filename in args.filenames:
        try:
            with open(filename, "rb") as openfile:
                _ = plistlib.load(openfile)
            # Possible future addition, but disabled for now.
            # if not isinstance(plist, dict):
            #     print(f"{filename}: top level of plist should be type dict")
            #     retval = 1
        except (ExpatError, ValueError) as err:
            print(f"{filename}: plist parsing error: {err}")
            retval = 1

    return retval


if __name__ == "__main__":
    exit(main())

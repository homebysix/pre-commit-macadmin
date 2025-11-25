#!/usr/bin/python
"""This hook auto-formats Property List (plist) files as XML."""

import argparse
import plistlib
from typing import List, Optional
from xml.parsers.expat import ExpatError


def build_argument_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser."""

    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("filenames", nargs="*", help="Filenames to format.")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Main process."""

    # Parse command line arguments.
    argparser = build_argument_parser()
    args = argparser.parse_args(argv)

    retval = 0
    for filename in args.filenames:
        try:
            # Read the plist file
            with open(filename, "rb") as openfile:
                plist_data = plistlib.load(openfile)

            # Write it back in XML format
            with open(filename, "wb") as openfile:
                plistlib.dump(
                    plist_data, openfile, fmt=plistlib.FMT_XML, sort_keys=True
                )
        except (ExpatError, ValueError) as err:
            print(f"{filename}: plist formatting error: {err}")
            retval = 1
        except Exception as err:
            print(f"{filename}: unexpected error: {err}")
            retval = 1

    return retval


if __name__ == "__main__":
    exit(main())

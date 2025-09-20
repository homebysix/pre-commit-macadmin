#!/usr/bin/python
"""Check Outset scripts to ensure they are executable."""

import argparse
import os
from typing import List, Optional

from pre_commit_macadmin_hooks.util import validate_shebangs


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
        if not os.access(filename, os.X_OK):
            print(f"{filename}: not executable")
            retval = 1

        # Ensure scripts have a proper shebang
        with open(filename, encoding="utf-8") as openfile:
            script_content = openfile.read()
        if not validate_shebangs(script_content, filename):
            print(f"{filename}: does not start with a valid shebang")
            retval = 1

    return retval


if __name__ == "__main__":
    exit(main())

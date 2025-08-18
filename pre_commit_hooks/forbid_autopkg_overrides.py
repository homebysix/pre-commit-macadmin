#!/usr/bin/python
"""This hook prevents AutoPkg overrides from being added to the repo."""

import argparse
from typing import List, Optional

from pre_commit_hooks.util import load_autopkg_recipe


def build_argument_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser."""

    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("filenames", nargs="*", help="Filenames to check.")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Main process."""

    # Overrides should not contain top-level Process arrays.
    required_keys = ("Process",)

    # Parse command line arguments.
    argparser = build_argument_parser()
    args = argparser.parse_args(argv)

    retval = 0
    for filename in args.filenames:
        recipe = load_autopkg_recipe(filename)
        if not recipe:
            retval = 1
            break  # No need to continue checking this file.
        for req_key in required_keys:
            if req_key not in recipe:
                print(f"{filename}: possible AutoPkg recipe override")
                retval = 1

    return retval


if __name__ == "__main__":
    exit(main())

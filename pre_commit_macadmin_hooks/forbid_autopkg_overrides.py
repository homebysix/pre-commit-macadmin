#!/usr/bin/python
"""This hook prevents AutoPkg overrides from being added to the repo."""

import argparse

from pre_commit_macadmin_hooks.util import load_autopkg_recipe


def build_argument_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser."""

    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("filenames", nargs="*", help="Filenames to check.")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Main process."""

    # Parse command line arguments.
    argparser = build_argument_parser()
    args = argparser.parse_args(argv)

    retval = 0
    for filename in args.filenames:
        recipe = load_autopkg_recipe(filename)
        if not recipe:
            retval = 1
            break  # No need to continue checking this file.
        # Overrides should not contain a top-level Process array.
        if "Process" not in recipe:
            print(f"{filename}: possible AutoPkg recipe override")
            retval = 1

    return retval


if __name__ == "__main__":
    exit(main())

#!/usr/bin/python
# -*- coding: utf-8 -*-
"""This hook prevents AutoPkg recipes with trust info from being added to the
repo."""

import argparse
from pre_commit_hooks.util import load_autopkg_recipe


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
        recipe = load_autopkg_recipe(filename)
        if not recipe:
            retval = 1
        elif "ParentRecipeTrustInfo" in recipe:
            print(f"{filename}: trust info in recipe")
            retval = 1

    return retval


if __name__ == "__main__":
    exit(main())

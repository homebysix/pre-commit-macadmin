#!/usr/bin/python
# -*- coding: utf-8 -*-
"""This hook runs the "makecatalogs" command to ensure all referenced packages
are present and catalogs are up to date."""

import argparse
import os
import subprocess


def build_argument_parser():
    """Build and return the argument parser."""

    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--munki-repo", default=".", help="Path to local Munki repo. (Defaults to '.')"
    )
    # TODO: Support makecatalogs options, ideally with kwargs for flexibility.
    return parser


def main(argv=None):
    """Main process."""

    # Path to makecatalogs.
    makecatalogs = "/usr/local/munki/makecatalogs"

    # Parse command line arguments.
    argparser = build_argument_parser()
    args = argparser.parse_args(argv)

    retval = 0
    if not os.path.isdir(os.path.join(args.munki_repo, "pkgsinfo")):
        print("Could not find pkgsinfo folder.")
        retval = 1
    elif not os.path.isfile(makecatalogs):
        print("{} does not exist.".format(makecatalogs))
        retval = 1
    else:
        retval = subprocess.call([makecatalogs, args.munki_repo])

    return retval


if __name__ == "__main__":
    exit(main())

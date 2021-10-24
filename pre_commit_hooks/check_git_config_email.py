#!/usr/bin/python
# -*- coding: utf-8 -*-
"""This hook checks to ensure the Git config email matches one of the specified domains."""

import argparse
import subprocess


def build_argument_parser():
    """Build and return the argument parser."""

    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--domains",
        nargs="+",
        help="One or more domains that the Git config email address must match.",
    )
    return parser


def main(argv=None):
    """Main process."""

    # Parse command line arguments.
    argparser = build_argument_parser()
    args = argparser.parse_args(argv)

    retval = 0
    if args.domains:
        user_email = subprocess.check_output(["git", "config", "--get", "user.email"])
        user_email = user_email.decode().strip()
        if not any((user_email.endswith(x) for x in args.domains)):
            print("Git config email is from an unexpected domain.")
            print("Git config email: " + user_email)
            print("Expected domains: " + str(args.domains))
            retval = 1

    return retval


if __name__ == "__main__":
    exit(main())

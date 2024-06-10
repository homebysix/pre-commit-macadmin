#!/usr/bin/python
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
        proc = subprocess.run(
            ["git", "config", "--get", "user.email"],
            check=False,
            capture_output=True,
            text=True,
        )
        user_email = proc.stdout.strip()
        if not user_email:
            print("Git config email is not set.")
            retval = 1
        elif "@" not in user_email:
            print("Git config email does not look like an email address.")
            print("Git config email: " + user_email)
            retval = 1
        elif not any((user_email.endswith("@" + x) for x in args.domains)):
            print("Git config email is from an unexpected domain.")
            print("Git config email: " + user_email)
            print("Expected domains: " + str(args.domains))
            retval = 1

    return retval


if __name__ == "__main__":
    exit(main())
